# A股实盘实战版策略（自定义参数）

## 策略参数配置

本策略使用以下**最终实战参数**：

| 指标 | 参数 | 说明 |
|------|------|------|
| VEGAS周期 | EMA144, EMA169, EMA576, EMA676 | 多重EMA组合判断趋势 |
| EMA12 | 12 | 短期突破过滤 |
| VWAP窗口 | 20 | 成本均价计算周期 |
| VOSC | 快线EMA1, 慢线EMA14 | 成交量能变化，上限150%，下限-80% |
| MACD | 12/26/9 | 背离确认指标 |
| 交易周期 | 5分钟/15分钟 | 日内短线交易 |

---

## 同花顺公式（自定义参数版）

```text
{ =========================================================
  A股实盘版：自定义参数EMA144/169/576/676组合策略
  交易周期：5分钟/15分钟
  参数：EMA144, EMA169, EMA576, EMA676, EMA12
  VWAP=20, VOSC快=1/慢=14, 上限150%下限-80%
  MACD=12/26/9
  ========================================================= }

{ ======== 核心参数 ======== }
EMA1 := 144;
EMA2 := 169;
EMA3 := 576;
EMA4 := 676;
EMA_SHORT := 12;
VWAP_N := 20;
VOSC_FAST := 1;
VOSC_SLOW := 14;
VOSC_UPPER := 150;    { 150% 上限 }
VOSC_LOWER := -80;    { -80% 下限 }
MACD_F := 12;
MACD_S := 26;
MACD_SIG := 9;

{ ======== 1. 多重EMA趋势判断 ======== }
{ 使用EMA144, EMA169, EMA576, EMA676判断趋势 }
MA144 := EMA(CLOSE, EMA1);
MA169 := EMA(CLOSE, EMA2);
MA576 := EMA(CLOSE, EMA3);
MA676 := EMA(CLOSE, EMA4);

{ 多头趋势：短期EMA>中期EMA>长期EMA }
TREND_UP := MA144 > MA169 AND MA169 > MA576 AND MA576 > MA676;
{ 空头趋势：短期EMA<中期EMA<长期EMA }
TREND_DOWN := MA144 < MA169 AND MA169 < MA576 AND MA576 < MA676;

{ ======== 2. EMA12突破过滤 ======== }
EMA12 := EMA(CLOSE, EMA_SHORT);
PRICE_ABOVE_EMA12 := CLOSE > EMA12;
PRICE_BELOW_EMA12 := CLOSE < EMA12;
EMA12_UP := EMA12 > REF(EMA12, 1);
EMA12_DOWN := EMA12 < REF(EMA12, 1);

{ 做多：价格在EMA12上方且EMA12上升 }
EMA12_BULL := PRICE_ABOVE_EMA12 AND EMA12_UP;
{ 做空：价格在EMA12下方且EMA12下降 }
EMA12_BEAR := PRICE_BELOW_EMA12 AND EMA12_DOWN;

{ ======== 3. VWAP成本均价 ======== }
TP := (HIGH + LOW + CLOSE) / 3;
VWAP := SUM(TP * VOL, VWAP_N) / SUM(VOL, VWAP_N);
VWAP_UP := VWAP > REF(VWAP, 1);
VWAP_DOWN := VWAP < REF(VWAP, 1);

{ ======== 4. VOSC体积能量（快=1，慢=14，含上下限） ======== }
{ 极度快速的成交量EMA组合 }
VOL_FAST := EMA(VOL, VOSC_FAST);
VOL_SLOW := EMA(VOL, VOSC_SLOW);
VOSC_RAW := VOL_FAST - VOL_SLOW;

{ VOSC百分比化（相对于VOL_SLOW）}
VOSC_PCT := IF(VOL_SLOW <> 0, (VOSC_RAW / VOL_SLOW) * 100, 0);

{ 应用上下限 }
VOSC := IF(VOSC_PCT > VOSC_UPPER, VOSC_UPPER, IF(VOSC_PCT < VOSC_LOWER, VOSC_LOWER, VOSC_PCT));

{ VOSC信号线（9周期） }
VOSC_SIG := EMA(VOSC, 9);

{ 多头量能：VOSC上升且高于信号线 }
VOSC_BULL := VOSC > VOSC_SIG AND VOSC > REF(VOSC, 1);
{ 空头量能：VOSC下降且低于信号线 }
VOSC_BEAR := VOSC < VOSC_SIG AND VOSC < REF(VOSC, 1);

{ ======== 5. MACD背离（12/26/9） ======== }
DIF := EMA(CLOSE, MACD_F) - EMA(CLOSE, MACD_S);
DEA := EMA(DIF, MACD_SIG);
MACD_BAR := 2 * (DIF - DEA);

{ 价格和DIF的背离判断（无未来函数） }
PRICE_LOW_20 := LLV(LOW, 20);
PRICE_HIGH_20 := HHV(HIGH, 20);
DIF_LOW_20 := LLV(DIF, 20);
DIF_HIGH_20 := HHV(DIF, 20);

{ 多头背离：价格创新低但DIF未创新低 }
BULL_DIV := LOW < REF(PRICE_LOW_20, 1) AND DIF > REF(DIF_LOW_20, 1) AND DIF > DEA;
{ 空头背离：价格创新高但DIF未创新高 }
BEAR_DIV := HIGH > REF(PRICE_HIGH_20, 1) AND DIF < REF(DIF_HIGH_20, 1) AND DIF < DEA;

{ ======== 6. A股交易过滤 ======== }
{ 非涨停/非跌停 }
NOT_LIMIT_UP := CLOSE < REF(CLOSE, 1) * 1.098;
NOT_LIMIT_DOWN := CLOSE > REF(CLOSE, 1) * 0.902;

{ 成交量有效性 }
VOL_VALID := VOL > 0 AND SUM(VOL, 5) > 0;

{ ======== 7. 综合买卖信号 ======== }
{ 多头信号：趋势+EMA12+VWAP+VOSC+MACD背离 }
BUY_SIGNAL := TREND_UP AND EMA12_BULL AND VWAP_UP AND VOSC_BULL AND BULL_DIV AND NOT_LIMIT_UP AND VOL_VALID;

{ 空头信号（参考，A股一般不用） }
SELL_SIGNAL := TREND_DOWN AND EMA12_BEAR AND VWAP_DOWN AND VOSC_BEAR AND BEAR_DIV AND NOT_LIMIT_DOWN AND VOL_VALID;

{ ======== 8. 止损规则 ======== }
{ 多头止损：跌破EMA12或关键EMA }
LONG_STOP := CLOSE < EMA12 OR CLOSE < VWAP;
{ 空头止损：突破EMA12或关键EMA }
SHORT_STOP := CLOSE > EMA12 OR CLOSE > VWAP;

{ ======== 9. 最终信号 ======== }
FINAL_BUY := BUY_SIGNAL AND NOT LONG_STOP;
FINAL_SELL := SELL_SIGNAL AND NOT SHORT_STOP;

{ ======== 10. 图表绘制 ======== }
DRAWLINE(MA144, LINESTICK, 2, RGB(255, 0, 0), 'EMA144');
DRAWLINE(MA169, LINESTICK, 2, RGB(255, 100, 0), 'EMA169');
DRAWLINE(MA576, LINESTICK, 2, RGB(0, 150, 255), 'EMA576');
DRAWLINE(MA676, LINESTICK, 2, RGB(0, 200, 150), 'EMA676');
DRAWLINE(EMA12, LINESTICK, 2, RGB(255, 200, 0), 'EMA12');
DRAWLINE(VWAP, LINESTICK, 2, RGB(200, 100, 255), 'VWAP');

IF(FINAL_BUY, DRAWICON(CLOSE, '↑', 'color:lime', 'size:18', '买入'));
IF(FINAL_SELL, DRAWICON(CLOSE, '↓', 'color:red', 'size:18', '卖出'));

{ ======== 11. 输出结果 ======== }
IF(FINAL_BUY, 1, 0);
IF(FINAL_SELL, -1, 0);
```

---

## Python回测程序（自定义参数版）

```python
import pandas as pd
import numpy as np
import sys
from pathlib import Path

class VegasStrategy:
    def __init__(self, initial_cash=100000, commission=0.0003, stamp_duty=0.0005, slippage=0.0005):
        # 交易参数
        self.initial_cash = initial_cash
        self.commission = commission
        self.stamp_duty = stamp_duty
        self.slippage = slippage
        
        # 策略参数（最终实战参数）
        self.ema1 = 144
        self.ema2 = 169
        self.ema3 = 576
        self.ema4 = 676
        self.ema_short = 12
        self.vwap_n = 20
        self.vosc_fast = 1
        self.vosc_slow = 14
        self.vosc_upper = 150  # 上限 150%
        self.vosc_lower = -80  # 下限 -80%
        self.macd_f = 12
        self.macd_s = 26
        self.macd_sig = 9

    def ema(self, series, period):
        if period <= 0:
            return series
        return series.ewm(span=period, adjust=False, min_periods=period).mean()

    def vwap(self, df, window=20):
        tp = (df['high'] + df['low'] + df['close']) / 3.0
        pv = tp * df['volume']
        return pv.rolling(window).sum() / df['volume'].rolling(window).sum()

    def compute_indicators(self, df):
        x = df.copy().sort_values('date').reset_index(drop=True)
        
        # 1. 多重EMA趋势
        x['ma144'] = self.ema(x['close'], self.ema1)
        x['ma169'] = self.ema(x['close'], self.ema2)
        x['ma576'] = self.ema(x['close'], self.ema3)
        x['ma676'] = self.ema(x['close'], self.ema4)
        
        x['trend_up'] = (
            (x['ma144'] > x['ma169']) &
            (x['ma169'] > x['ma576']) &
            (x['ma576'] > x['ma676'])
        )
        x['trend_down'] = (
            (x['ma144'] < x['ma169']) &
            (x['ma169'] < x['ma576']) &
            (x['ma576'] < x['ma676'])
        )

        # 2. EMA12
        x['ema12'] = self.ema(x['close'], self.ema_short)
        x['ema12_bull'] = (x['close'] > x['ema12']) & (x['ema12'] > x['ema12'].shift(1))
        x['ema12_bear'] = (x['close'] < x['ema12']) & (x['ema12'] < x['ema12'].shift(1))

        # 3. VWAP
        x['vwap'] = self.vwap(x, window=self.vwap_n)
        x['vwap_up'] = x['vwap'] > x['vwap'].shift(1)
        x['vwap_down'] = x['vwap'] < x['vwap'].shift(1)

        # 4. VOSC（快=1，慢=14，含上下限）
        vol_fast = self.ema(x['volume'], self.vosc_fast)
        vol_slow = self.ema(x['volume'], self.vosc_slow)
        vosc_raw = vol_fast - vol_slow
        
        # 百分比化
        x['vosc_pct'] = np.where(
            vol_slow != 0,
            (vosc_raw / vol_slow) * 100,
            0
        )
        
        # 应用上下限
        x['vosc'] = x['vosc_pct'].clip(lower=self.vosc_lower, upper=self.vosc_upper)
        x['vosc_sig'] = self.ema(x['vosc'], 9)
        
        x['vosc_bull'] = (x['vosc'] > x['vosc_sig']) & (x['vosc'] > x['vosc'].shift(1))
        x['vosc_bear'] = (x['vosc'] < x['vosc_sig']) & (x['vosc'] < x['vosc'].shift(1))

        # 5. MACD（12/26/9）
        dif = self.ema(x['close'], self.macd_f) - self.ema(x['close'], self.macd_s)
        dea = self.ema(dif, self.macd_sig)
        
        x['dif'] = dif
        x['dea'] = dea
        x['macd'] = 2 * (dif - dea)

        # 价格和DIF背离
        x['price_low_20'] = x['low'].rolling(20).min()
        x['price_high_20'] = x['high'].rolling(20).max()
        x['dif_low_20'] = x['dif'].rolling(20).min()
        x['dif_high_20'] = x['dif'].rolling(20).max()

        x['bull_div'] = (
            (x['low'] < x['price_low_20'].shift(1)) &
            (x['dif'] > x['dif_low_20'].shift(1)) &
            (x['dif'] > x['dea'])
        )
        x['bear_div'] = (
            (x['high'] > x['price_high_20'].shift(1)) &
            (x['dif'] < x['dif_high_20'].shift(1)) &
            (x['dif'] < x['dea'])
        )

        # A股过滤
        x['not_limit_up'] = x['close'] < x['close'].shift(1) * 1.098
        x['not_limit_down'] = x['close'] > x['close'].shift(1) * 0.902
        x['vol_valid'] = (x['volume'] > 0) & (x['volume'].rolling(5).sum() > 0)

        # 买卖信号
        x['buy_signal'] = (
            x['trend_up'] &
            x['ema12_bull'] &
            x['vwap_up'] &
            x['vosc_bull'] &
            x['bull_div'] &
            x['not_limit_up'] &
            x['vol_valid']
        )

        x['sell_signal'] = (
            x['trend_down'] &
            x['ema12_bear'] &
            x['vwap_down'] &
            x['vosc_bear'] &
            x['bear_div'] &
            x['not_limit_down'] &
            x['vol_valid']
        )

        return x.dropna().reset_index(drop=True)

    def backtest(self, df):
        x = self.compute_indicators(df)
        
        cash = self.initial_cash
        shares = 0
        entry_price = 0.0
        stop_price = 0.0
        peak_price = 0.0
        
        trades = []
        equity_curve = []
        
        for i in range(1, len(x)):
            current = x.iloc[i]
            prev = x.iloc[i-1]
            
            # 卖出逻辑：前日信号生效，今日开盘执行
            if shares > 0:
                exit_triggered = (
                    bool(prev['sell_signal']) or
                    current['close'] < current['ema12'] or
                    current['close'] < current['vwap'] or
                    current['dif'] < current['dea']
                )
                
                if exit_triggered:
                    sell_price = current['open'] * (1 - self.slippage)
                    proceeds = shares * sell_price
                    total_fee = proceeds * (self.commission + self.stamp_duty)
                    cash += proceeds - total_fee
                    
                    trades.append({
                        'date': current['date'],
                        'type': 'SELL',
                        'price': sell_price,
                        'shares': shares,
                        'fee': total_fee,
                        'pnl': proceeds - (shares * entry_price * (1 + self.commission))
                    })
                    
                    shares = 0
                    entry_price = 0.0
                    stop_price = 0.0
                    peak_price = 0.0

            # 买入逻辑：前日信号生效，今日开盘执行
            if shares == 0 and bool(prev['buy_signal']):
                buy_price = current['open'] * (1 + self.slippage)
                
                # 不追涨停附近
                if buy_price < current['close'] * 1.098:
                    max_qty = int((cash * 0.95) / (buy_price * (1 + self.commission)) / 100) * 100
                    
                    if max_qty > 0:
                        qty = max_qty
                        total_cost = qty * buy_price * (1 + self.commission)
                        cash -= total_cost
                        
                        shares = qty
                        entry_price = buy_price
                        peak_price = buy_price
                        stop_price = buy_price * 0.98  # 初始止损 2%
                        
                        trades.append({
                            'date': current['date'],
                            'type': 'BUY',
                            'price': buy_price,
                            'shares': qty,
                            'fee': qty * buy_price * self.commission,
                            'pnl': 0.0
                        })

            # 记录权益曲线
            equity = cash + (shares * current['close'] if shares > 0 else 0)
            equity_curve.append({
                'date': current['date'],
                'close': current['close'],
                'equity': equity,
                'cash': cash,
                'shares': shares,
                'ma144': current['ma144'],
                'ema12': current['ema12'],
                'vwap': current['vwap'],
                'vosc': current['vosc'],
                'dif': current['dif']
            })

        return pd.DataFrame(equity_curve), pd.DataFrame(trades)

    def evaluate(self, curve, trades):
        if curve.empty:
            return {}
        
        final_equity = curve['equity'].iloc[-1]
        total_return = (final_equity / self.initial_cash - 1) * 100
        
        curve['peak'] = curve['equity'].cummax()
        curve['drawdown'] = (curve['equity'] / curve['peak'] - 1) * 100
        max_drawdown = curve['drawdown'].min()
        
        if not trades.empty:
            buy_trades = trades[trades['type'] == 'BUY']
            sell_trades = trades[trades['type'] == 'SELL']
            trade_count = len(sell_trades)
            pnl_trades = sell_trades[sell_trades['pnl'].notna()]
            
            if len(pnl_trades) > 0:
                win_count = (pnl_trades['pnl'] > 0).sum()
                win_rate = (win_count / len(pnl_trades) * 100) if len(pnl_trades) > 0 else 0
            else:
                win_rate = 0
        else:
            trade_count = 0
            win_rate = 0
        
        stats = {
            'initial_cash': self.initial_cash,
            'final_equity': round(final_equity, 2),
            'total_return_%': round(total_return, 2),
            'max_drawdown_%': round(max_drawdown, 2),
            'trade_count': trade_count,
            'win_rate_%': round(win_rate, 2)
        }
        
        return stats

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python backtest_vegas.py <data.csv> [initial_cash]")
        print("示例: python backtest_vegas.py data.csv 100000")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    initial_cash = float(sys.argv[2]) if len(sys.argv) > 2 else 100000
    
    if not Path(csv_file).exists():
        print(f"文件不存在: {csv_file}")
        sys.exit(1)
    
    # 读取数据（必须包含 date, open, high, low, close, volume 列）
    df = pd.read_csv(csv_file, parse_dates=['date'])
    
    # 运行回测
    strategy = VegasStrategy(initial_cash=initial_cash)
    curve, trades = strategy.backtest(df)
    stats = strategy.evaluate(curve, trades)
    
    # 输出结果
    print("\n" + "="*60)
    print("A股VEGAS策略回测结果（自定义参数版）")
    print("="*60)
    for key, val in stats.items():
        print(f"{key:.<30} {val}")
    print("="*60 + "\n")
    
    # 保存结果到CSV
    curve.to_csv('equity_curve.csv', index=False)
    trades.to_csv('trades.csv', index=False)
    
    print("已保存:")
    print("  - equity_curve.csv （权益曲线）")
    print("  - trades.csv （交易记录）")
    print(f"\n最近10笔交易:")
    print(trades.tail(10).to_string())
```

---

## 使用说明

### 同花顺中使用

1. 打开同花顺 → **公式** → **新建**
2. 复制上述公式代码
3. 选择 **5分钟** 或 **15分钟** K线周期
4. 点击 **应用** 即可看到实时信号

### Python回测

1. 准备CSV数据文件（必须包含字段: `date,open,high,low,close,volume`）
   
   ```csv
   date,open,high,low,close,volume
   2024-01-01 09:30:00,3000,3050,2980,3020,10000000
   2024-01-01 09:35:00,3020,3080,3010,3050,12000000
   ...
   ```

2. 运行回测

   ```bash
   python backtest_vegas.py data.csv 100000
   ```

3. 查看结果
   - 控制台输出策略统计
   - `equity_curve.csv` 权益曲线
   - `trades.csv` 交易记录

---

## 关键参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| EMA144 | 144 | 超长期趋势（≈144分钟/日内） |
| EMA169 | 169 | 长期趋势 |
| EMA576 | 576 | 中期趋势 |
| EMA676 | 676 | 极长期基准线 |
| EMA12 | 12 | 短期突破确认 |
| VWAP窗口 | 20 | 成本均价周期 |
| VOSC快 | 1 | 极快成交量反应 |
| VOSC慢 | 14 | 成交量慢线 |
| VOSC上限 | 150% | 过热卖压过滤 |
| VOSC下限 | -80% | 过度悲观过滤 |
| MACD | 12/26/9 | 标准MACD背离判断 |
| 交易周期 | 5分钟/15分钟 | 日内短线 |

---

## 风险提示

1. **仅供研究**：本策略不构成投资建议
2. **参数风险**：自定义参数可能在不同市场环境失效
3. **A股限制**：
   - 只做多，不做空
   - T+1 交易制度
   - 涨跌停限制
   - 停牌风险
4. **滑点/手续费**：回测已计入，但实盘可能有偏差
5. **样本外风险**：历史回测不保证未来收益

---

## 后续优化方向

- [ ] 加入动态止损（ATR跟踪）
- [ ] 加入日间/日线结合策略
- [ ] 加入板块/个股选择过滤
- [ ] 多品种组合回测
- [ ] 实时信号推送接口
