# VEGAS通道交易策略（完整版）

## 一、策略说明

本策略按照以下流程执行：

1. VEGAS通道 → 判断趋势方向
2. EMA12过滤 → 过滤真假突破
3. VWAP斜率 → 判断成本方向
4. VOSC变化 → 判断成交量能大小变化
5. MACD背离 → 确定最终入场时机

适用于：
- 中国大陆A股（以多头为主）
- 指数、ETF、强势个股
- 思路用于回测和量化策略研究

> 免责声明：仅用于学习、研究和回测，不构成投资建议。

---

## 二、同花顺公式（完整版）

```text
{ =========================================================
  VEGAS趋势 + EMA12 + VWAP + VOSC + MACD 综合策略（完整版）
  用途：A股/指数/ETF趋势交易信号
  适合：同花顺公式编辑器直接使用
  说明：
  1. VEGAS通道判断趋势方向
  2. EMA12过滤真假突破
  3. VWAP斜率判断成本方向
  4. VOSC判断量能扩张/萎缩
  5. MACD背离确认最终入场时机
  ========================================================= }

{ =========================
  1. VEGAS通道
  ========================= }
VEGAS_N := 14;
UpperBand := EMA(HIGH, VEGAS_N);
LowerBand := EMA(LOW, VEGAS_N);
MiddleBand := (UpperBand + LowerBand) / 2;

TrendUp := CLOSE > MiddleBand AND MiddleBand > REF(MiddleBand, 1);
TrendDown := CLOSE < MiddleBand AND MiddleBand < REF(MiddleBand, 1);

{ =========================
  2. EMA12过滤
  ========================= }
EMA12 := EMA(CLOSE, 12);
EMA12_Bull := CLOSE > EMA12 AND EMA12 > REF(EMA12, 1);
EMA12_Bear := CLOSE < EMA12 AND EMA12 < REF(EMA12, 1);

{ =========================
  3. VWAP斜率（滚动）
  ========================= }
VWAP_N := 20;
TypicalPrice := (HIGH + LOW + CLOSE) / 3;
VWAP := SUM(TypicalPrice * VOL, VWAP_N) / SUM(VOL, VWAP_N);
VWAP_Bull := VWAP > REF(VWAP, 1);
VWAP_Bear := VWAP < REF(VWAP, 1);

{ =========================
  4. VOSC量能变化
  ========================= }
VOSC_FAST := 12;
VOSC_SLOW := 26;
VOSC_SIG := 9;

VOL_FAST := EMA(VOL, VOSC_FAST);
VOL_SLOW := EMA(VOL, VOSC_SLOW);
VOSC := VOL_FAST - VOL_SLOW;
VOSC_SIGLINE := EMA(VOSC, VOSC_SIG);
VOSC_Bull := VOSC > VOSC_SIGLINE AND VOSC > REF(VOSC, 1);
VOSC_Bear := VOSC < VOSC_SIGLINE AND VOSC < REF(VOSC, 1);

{ =========================
  5. MACD背离
  ========================= }
MACD_FAST := 12;
MACD_SLOW := 26;
MACD_SIG := 9;
DIF := EMA(CLOSE, MACD_FAST) - EMA(CLOSE, MACD_SLOW);
DEA := EMA(DIF, MACD_SIG);
MACD_BAR := 2 * (DIF - DEA);

PriceLow10 := LLV(LOW, 10);
PriceHigh10 := HHV(HIGH, 10);
DIFLow10 := LLV(DIF, 10);
DIFHigh10 := HHV(DIF, 10);

BullishDivergence := LOW < PriceLow10 AND DIF > DIFLow10 AND DIF > DEA;
BearishDivergence := HIGH > PriceHigh10 AND DIF < DIFHigh10 AND DIF < DEA;

{ =========================
  6. 止损/止盈（建议）
  ========================= }
{ 以中轨作为止损参考：
  多头止损：价格跌破中轨
  空头止损：价格突破中轨
}
StopLossLong := CLOSE < MiddleBand;
StopLossShort := CLOSE > MiddleBand;

{ =========================
  7. 综合买卖信号
  ========================= }
BuySignal := TrendUp AND EMA12_Bull AND VWAP_Bull AND VOSC_Bull AND BullishDivergence AND NOT(StopLossLong);
SellSignal := TrendDown AND EMA12_Bear AND VWAP_Bear AND VOSC_Bear AND BearishDivergence AND NOT(StopLossShort);

{ =========================
  8. 图表输出
  ========================= }
DRAWLINE(UpperBand, LINESTICK, 2, RGB(255, 0, 0), 'VEGAS上轨');
DRAWLINE(MiddleBand, LINESTICK, 2, RGB(0, 120, 255), 'VEGAS中轨');
DRAWLINE(LowerBand, LINESTICK, 2, RGB(0, 200, 100), 'VEGAS下轨');
DRAWLINE(EMA12, LINESTICK, 2, RGB(255, 180, 0), 'EMA12');
DRAWLINE(VWAP, LINESTICK, 2, RGB(255, 120, 0), 'VWAP');

IF(BuySignal, DRAWICON(CLOSE, '↑', 'color:green', 'size:18', '买入'));
IF(SellSignal, DRAWICON(CLOSE, '↓', 'color:red', 'size:18', '卖出'));

{ =========================
  9. 输出结果值
  ========================= }
IF(BuySignal, 1, 0);
IF(SellSignal, -1, 0);
```

注意：
- 这段代码适合先做“信号验证”，适合同花顺公式测试。
- A股手续费、滑点、涨跌停、T+1以及停牌会影响实际交易。
- 不建议直接用单一站点信号完全实盘。

---

## 三、Python回测版（完整版）

```python
import pandas as pd
import numpy as np


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def vwap(df: pd.DataFrame, window: int = 20) -> pd.Series:
    tp = (df['high'] + df['low'] + df['close']) / 3.0
    pv = tp * df['volume']
    vwap = pv.rolling(window).sum() / df['volume'].rolling(window).sum()
    return vwap


def vegas_band(df: pd.DataFrame, n: int = 14):
    upper = ema(df['high'], n)
    lower = ema(df['low'], n)
    middle = (upper + lower) / 2.0
    return upper, middle, lower


def calc_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    dif = ema(df['close'], fast) - ema(df['close'], slow)
    dea = ema(dif, signal)
    macd = 2 * (dif - dea)
    return dif, dea, macd


def calc_vosc(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    vol_fast = ema(df['volume'], fast)
    vol_slow = ema(df['volume'], slow)
    vosc = vol_fast - vol_slow
    vosc_signal = ema(vosc, signal)
    return vosc, vosc_signal


def compute_strategy(df: pd.DataFrame):
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)

    # 1) VEGAS
    upper, middle, lower = vegas_band(df, n=14)
    df['vegas_upper'] = upper
    df['vegas_middle'] = middle
    df['vegas_lower'] = lower
    df['trend_up'] = (df['close'] > df['vegas_middle']) & (df['vegas_middle'] > df['vegas_middle'].shift(1))
    df['trend_down'] = (df['close'] < df['vegas_middle']) & (df['vegas_middle'] < df['vegas_middle'].shift(1))

    # 2) EMA12
    ema12 = ema(df['close'], 12)
    df['ema12'] = ema12
    df['ema12_long'] = (df['close'] > df['ema12']) & (df['ema12'] > df['ema12'].shift(1))
    df['ema12_short'] = (df['close'] < df['ema12']) & (df['ema12'] < df['ema12'].shift(1))

    # 3) VWAP
    df['vwap'] = vwap(df, window=20)
    df['vwap_long'] = df['vwap'] > df['vwap'].shift(1)
    df['vwap_short'] = df['vwap'] < df['vwap'].shift(1)

    # 4) VOSC
    vosc, vosc_signal = calc_vosc(df, 12, 26, 9)
    df['vosc'] = vosc
    df['vosc_signal'] = vosc_signal
    df['vosc_long'] = (df['vosc'] > df['vosc_signal']) & (df['vosc'] > df['vosc'].shift(1))
    df['vosc_short'] = (df['vosc'] < df['vosc_signal']) & (df['vosc'] < df['vosc'].shift(1))

    # 5) MACD
    dif, dea, macd = calc_macd(df, 12, 26, 9)
    df['dif'] = dif
    df['dea'] = dea
    df['macd'] = macd

    # 价格与DIF背离
    df['low_10'] = df['low'].rolling(10).min()
    df['high_10'] = df['high'].rolling(10).max()
    df['dif_low_10'] = df['dif'].rolling(10).min()
    df['dif_high_10'] = df['dif'].rolling(10).max()

    df['bull_div'] = (df['low'] < df['low_10'].shift(1)) & (df['dif'] > df['dif_low_10'].shift(1)) & (df['dif'] > df['dea'])
    df['bear_div'] = (df['high'] > df['high_10'].shift(1)) & (df['dif'] < df['dif_high_10'].shift(1)) & (df['dif'] < df['dea'])

    # 6) 交易信号
    df['buy_signal'] = (
        df['trend_up'] &
        df['ema12_long'] &
        df['vwap_long'] &
        df['vosc_long'] &
        df['bull_div']
    )

    df['sell_signal'] = (
        df['trend_down'] &
        df['ema12_short'] &
        df['vwap_short'] &
        df['vosc_short'] &
        df['bear_div']
    )

    return df


def evaluate_strategy(df: pd.DataFrame):
    df = compute_strategy(df)

    # 交易状态模拟（简化版）
    cash = 100000.0
    position = 0
    holdings = 0.0
    trade_log = []
    total_fee = 0.0

    for i in range(1, len(df)):
        close = df.loc[i, 'close']
        if df.loc[i, 'buy_signal'] and position == 0:
            # 以收盘价买入
            qty = cash / close
            holdings = qty
            position = 1
            trade_log.append({'date': df.loc[i, 'date'], 'type': 'buy', 'price': close, 'qty': qty})
        elif df.loc[i, 'sell_signal'] and position == 1:
            cash = holdings * close * (1 - 0.0008)
            total_fee += holdings * close * 0.0008
            position = 0
            holdings = 0.0
            trade_log.append({'date': df.loc[i, 'date'], 'type': 'sell', 'price': close, 'qty': qty if 'qty' in locals() else 0})

    final_value = cash + holdings * df.iloc[-1]['close']
    print('最终净值:', round(final_value, 2))
    print('累计手续费:', round(total_fee, 2))
    print('交易次数:', len(trade_log))
    return df, trade_log


if __name__ == '__main__':
    # 读取示例：字段要求: date, open, high, low, close, volume
    # df = pd.read_csv('data.csv', parse_dates=['date'])
    # df = df.sort_values('date').reset_index(drop=True)
    # result, trades = evaluate_strategy(df)
    # print(result[['date', 'close', 'buy_signal', 'sell_signal']].tail(20))
    pass
```

---

## 四、实战落地建议（非常关键）

1. 先做“同花顺公式验证”，不要直接实盘
2. 先用 15 分钟/30 分钟/日线测试参数稳定性
3. 只看强趋势股票，不要在弱市中强行做多
4. 建议在以下条件下放大信号质量：
   - 成交量放大
   - 价格站稳均线
   - 盘中不破VEGAS下轨
5. 加入止损：
   - 长线：跌破VEGAS中轨止损
   - 日内：回落到VWAP下方或EMA12下方止损
6. 资金管理：
   - 单次交易不超过账户 1%
   - 连续亏损不继续加码

---

## 五、总结

这个策略的核心不是“看某一个指标”，而是：

- 趋势方向：VEGAS通道
- 真突破过滤：EMA12
- 成本方向：VWAP斜率
- 量能变化：VOSC
- 最终入场：MACD背离

这是一种多层过滤的“趋势跟随 + 量能确认 + 背离确认”的策略思路。

如果你需要下一步，我可以继续直接给你：

- 同花顺“实盘版更稳公式”（带止损/止盈）
- Python 完整回测代码（读取CSV并输出胜率/收益/最大回撤）
- A股实战版参数优化模板

你只要回复：
- “实盘版公式”
- “完整回测”
- “参数优化”

我就继续。