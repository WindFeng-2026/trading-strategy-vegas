from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class Config:
    initial_cash: float = 100_000.0
    commission: float = 0.0003
    stamp_duty: float = 0.0005
    slippage: float = 0.0005
    risk_per_trade: float = 0.01
    max_position_pct: float = 0.95
    atr_period: int = 14
    stop_atr_multiple: float = 2.0
    trail_atr_multiple: float = 2.5
    vegas_period: int = 14
    vwap_period: int = 20


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def indicators(df: pd.DataFrame, c: Config) -> pd.DataFrame:
    x = df.copy()
    x.columns = [str(v).lower().strip() for v in x.columns]
    required = {"date", "open", "high", "low", "close", "volume"}
    missing = required - set(x.columns)
    if missing:
        raise ValueError(f"缺少字段: {sorted(missing)}")
    x = x.sort_values("date").drop_duplicates("date").reset_index(drop=True)

    x["vup"] = ema(x.high, c.vegas_period)
    x["vdn"] = ema(x.low, c.vegas_period)
    x["vmid"] = (x.vup + x.vdn) / 2
    x["trend"] = (x.close > x.vmid) & (x.vmid > x.vmid.shift(1))

    x["ema12"] = ema(x.close, 12)
    x["ema_ok"] = (x.close > x.ema12) & (x.ema12 > x.ema12.shift(1))
    x["breakout"] = (x.close > x.ema12) & (x.close.shift(1) <= x.ema12.shift(1))

    tp = (x.high + x.low + x.close) / 3
    x["vwap"] = (tp * x.volume).rolling(c.vwap_period).sum() / x.volume.rolling(c.vwap_period).sum()
    x["vwap_ok"] = x.vwap > x.vwap.shift(1)

    x["vosc"] = ema(x.volume, 12) - ema(x.volume, 26)
    x["vosc_sig"] = ema(x.vosc, 9)
    x["vosc_ok"] = (x.vosc > x.vosc_sig) & (x.vosc > x.vosc.shift(1))

    x["dif"] = ema(x.close, 12) - ema(x.close, 26)
    x["dea"] = ema(x.dif, 9)
    x["macd_ok"] = (x.dif > x.dea) & (x.dif > x.dif.shift(1))
    # 简化、无未来函数的滚动背离代理：当前窗口价格创新低而DIF未创新低。
    x["bull_div"] = (x.low < x.low.rolling(20).min().shift(1)) & (
        x.dif > x.dif.rolling(20).min().shift(1)
    )

    prev_close = x.close.shift(1)
    tr = pd.concat([x.high - x.low, (x.high - prev_close).abs(), (x.low - prev_close).abs()], axis=1).max(axis=1)
    x["atr"] = tr.rolling(c.atr_period).mean()
    x["buy_signal"] = x[["trend", "ema_ok", "breakout", "vwap_ok", "vosc_ok", "macd_ok", "bull_div"]].all(axis=1)
    x["exit_signal"] = (x.close < x.vmid) | (x.close < x.ema12) | (x.close < x.vwap) | (x.dif < x.dea)
    return x.dropna().reset_index(drop=True)


def backtest(data: pd.DataFrame, c: Config = Config()):
    x = indicators(data, c)
    cash, shares, entry_price, stop, peak = c.initial_cash, 0, 0.0, 0.0, 0.0
    equity_rows, trades = [], []
    can_sell = False  # T+1：成交后下一根K线才允许卖出

    for i in range(1, len(x)):
        row, prev = x.iloc[i], x.iloc[i - 1]
        equity = cash + shares * row.close

        # 先处理卖出：使用今日开盘，信号来自前一日收盘；止损使用当日开盘近似。
        if shares > 0:
            peak = max(peak, row.high)
            trail = peak - c.trail_atr_multiple * row.atr
            stop = max(stop, trail)
            limit_down = row.open <= prev.close * 0.90 + 1e-12
            should_exit = bool(prev.exit_signal) or row.open <= stop
            if can_sell and should_exit and not limit_down:
                price = row.open * (1 - c.slippage)
                gross = shares * price
                fee = gross * (c.commission + c.stamp_duty)
                cash += gross - fee
                trades.append({"date": row.date, "side": "SELL", "price": price, "shares": shares, "fee": fee, "reason": "signal_or_stop"})
                shares, entry_price, stop, peak, can_sell = 0, 0.0, 0.0, 0.0, False

        # 再处理买入：前一日收盘确认，今日开盘成交；涨停不追买。
        if shares == 0 and bool(prev.buy_signal):
            limit_up = row.open >= prev.close * 1.10 - 1e-12
            price = row.open * (1 + c.slippage)
            risk_per_share = max(prev.atr * c.stop_atr_multiple, price * 0.02)
            risk_budget = cash * c.risk_per_trade
            by_risk = int(risk_budget / risk_per_share) if risk_per_share > 0 else 0
            by_cash = int(cash * c.max_position_pct / (price * (1 + c.commission)))
            qty = max(0, min(by_risk, by_cash) // 100 * 100)  # A股按100股整数倍
            if qty > 0 and not limit_up:
                gross = qty * price
                fee = gross * c.commission
                cash -= gross + fee
                shares, entry_price, peak = qty, price, price
                stop = price - prev.atr * c.stop_atr_multiple
                can_sell = False
                trades.append({"date": row.date, "side": "BUY", "price": price, "shares": qty, "fee": fee, "reason": "five_filter_signal"})

        equity_rows.append({"date": row.date, "equity": cash + shares * row.close, "cash": cash, "shares": shares})
        if shares > 0:
            can_sell = True

    curve = pd.DataFrame(equity_rows)
    if curve.empty:
        return curve, pd.DataFrame(trades), {}
    curve["peak"] = curve.equity.cummax()
    curve["drawdown"] = curve.equity / curve.peak - 1
    sell_trades = pd.DataFrame(trades)
    stats = {
        "initial_cash": c.initial_cash,
        "final_equity": float(curve.equity.iloc[-1]),
        "return": float(curve.equity.iloc[-1] / c.initial_cash - 1),
        "max_drawdown": float(curve.drawdown.min()),
        "trade_count": int(len(trades)),
        "sell_count": int((sell_trades.side == "SELL").sum()) if not sell_trades.empty else 0,
    }
    return curve, sell_trades, stats


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("用法: python backtest_a_share.py data.csv")
    path = Path(sys.argv[1])
    curve, trades, stats = backtest(pd.read_csv(path, parse_dates=["date"]))
    print(pd.Series(stats).to_string())
    curve.to_csv("equity_curve.csv", index=False)
    trades.to_csv("trades.csv", index=False)
    print("已输出 equity_curve.csv 和 trades.csv")
