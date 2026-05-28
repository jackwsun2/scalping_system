# 超短线量化交易系统 (Scalping Trading System)

基于 Python 的专业级美股超短线（Day Trading / Scalping）量化交易系统，支持历史回测和实盘交易。

## 📋 系统特性

✅ **数据层**
- yfinance 自动获取美股数据（GLD, SLV, QQQ 等）
- 支持多种时间频率（1分钟、5分钟、1小时、1天）

✅ **信号计算**
- RSI (相对强度指标)
- MACD (移动平均收敛散度)
- 布林带 (Bollinger Bands)
- ATR (平均真实波幅)

✅ **交易策略**
- 超短线结合多指标信号
- RSI 超卖/超买
- MACD 金叉/死叉
- 布林带突破
- 可配置的止损和目标

✅ **回测系统**
- 向量化高性能回测
- 胜率、收益率、夏普比率计算
- 滑点和佣金模拟
- 最大回撤分析

✅ **实盘执行**
- Alpaca API 对接
- 支持模拟盘 (Paper Trading) 和实盘
- 市价单和限价单

✅ **监控告警**
- Telegram 推送交易信号
- 实时价格提醒

## 🚀 快速开始

### 1. 系统要求

- macOS 或 Linux / Windows
- Python 3.8+
- pip 或 conda

### 2. 安装依赖

```bash
cd scalping_system
pip install -r requirements.txt
```

如果遇到 TA-Lib 安装问题，可以跳过，系统会使用 pandas-ta 作为备选。

### 3. 配置

复制示例配置文件：

```bash
cp config/example_config.py config/config.py
```

编辑 `config/config.py`，填入你的参数：

```python
# 交易配置
TRADING_CONFIG = {
    'symbols': ['GLD', 'SLV'],  # 监控的股票代码
    'interval': '5m',            # 5分钟K线
    'quantity': 10,              # 每次10股
}

# Alpaca API 配置 (如需实盘)
ALPACA_CONFIG = {
    'api_key': 'YOUR_API_KEY',
    'secret_key': 'YOUR_SECRET_KEY',
    'base_url': 'https://paper-api.alpaca.markets',  # 模拟盘
}

# Telegram 推送 (可选)
TELEGRAM_CONFIG = {
    'bot_token': 'YOUR_BOT_TOKEN',
    'chat_id': 'YOUR_CHAT_ID',
    'enabled': False,  # 启用后可接收信号推送
}
```

### 4. 运行系统

```bash
python src/main.py
```

系统会提示选择模式：

```
Select mode:
1. Backtest (历史回测)
2. Live Trading (实盘/模拟盘)
```

#### 4.1 回测模式

运行历史数据回测，评估策略表现：

```
Choice (1 or 2): 1
```

输出结果包括：
- 总收益率
- 胜率
- 最大回撤
- 夏普比率
- 每笔交易的详细信息

#### 4.2 实盘模式

连接 Alpaca API 进行实时监控和交易执行：

```
Choice (1 or 2): 2
```

默认使用 **模拟盘 (Paper Trading)**，可安全测试策略。

## 📁 项目结构

```
scalping_system/
├── src/
│   ├── main.py              # 主程序入口
│   ├── config.py            # 配置管理
│   ├── data_fetcher.py      # 数据获取 (yfinance)
│   ├── indicators.py        # 技术指标计算 (pandas-ta)
│   ├── strategy.py          # 交易策略逻辑
│   ├── backtest.py          # 回测引擎
│   ├── executor.py          # 订单执行 (Alpaca API)
│   └── alerts.py            # Telegram 告警推送
├── config/
│   └── example_config.py    # 配置示例
├── tests/                   # 测试文件夹
├── logs/                    # 日志文件夹 (自动创建)
├── requirements.txt         # 依赖列表
└── README.md               # 本文件
```

## 🔧 配置说明

### 交易配置 (TRADING_CONFIG)

| 参数 | 说明 | 示例 |
|------|------|------|
| `symbols` | 监控的股票代码列表 | `['GLD', 'SLV', 'QQQ']` |
| `interval` | K线周期 | `'5m'`, `'1h'`, `'1d'` |
| `quantity` | 每笔订单股数 | `10` |
| `max_position` | 最大持仓数 | `100` |

### 策略参数 (STRATEGY_CONFIG)

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `rsi_period` | RSI 周期 | 14 |
| `rsi_oversold` | RSI 超卖阈值 | 30 |
| `rsi_overbought` | RSI 超买阈值 | 70 |
| `stop_loss_pct` | 止损百分比 | 1.0% |
| `take_profit_pct` | 止盈百分比 | 2.0% |

### 回测参数 (BACKTEST_CONFIG)

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `initial_cash` | 初始资金 | $10,000 |
| `slippage` | 滑点百分比 | 0.01% |
| `commission` | 单笔佣金 | $0 (Alpaca 免佣金) |

## 📊 典型回测输出

```
============================================================
Backtest Results for GLD
============================================================
Total Return: +15.32%
Win Rate: 62.50%
Total Trades: 48
Winning Trades: 30
Losing Trades: 18
Avg Win: $12.45
Avg Loss: $-8.23
Profit Factor: 1.86
Max Drawdown: -8.12%
Sharpe Ratio: 1.45
Sortino Ratio: 2.13

First 5 Trades:
  Trade 1: Entry: $189.45, Exit: $191.23, Profit: +$17.80 (+1.88%)
  Trade 2: Entry: $191.50, Exit: $189.80, Profit: -$17.00 (-0.89%)
  ...
```

## 🔐 API 配置

### Alpaca 账户设置

1. 注册 [Alpaca Markets](https://app.alpaca.markets/)
2. 获取 API Key 和 Secret Key
3. 填入 `config.py`

### Telegram Bot 设置

1. 添加 [@BotFather](https://t.me/botfather) 为 Telegram 好友
2. 发送命令 `/newbot` 创建新 bot
3. 获取 bot token
4. 向你的 bot 发送 `/start` 获取 chat_id
5. 在配置中启用并填入相关信息

## ⚠️ 重要提示

### 风险警告

量化交易涉及高风险，可能导致全部亏损。在使用本系统前：

1. **充分理解策略逻辑** - 修改参数需要理解其含义
2. **充分的回测** - 在实盘前至少用3-6个月历史数据回测
3. **小额实盘测试** - 从最小订单量开始
4. **持续监控** - 不要完全自动化，定期检查系统运行
5. **风险管理** - 使用止损和风险控制参数

### 系统限制

- yfinance 数据可能有延迟
- 美股交易时间: 周一-周五 9:30 AM - 4:00 PM EST
- Alpaca API 有请求频率限制 (Rate Limit)
- 超短线交易对延迟敏感，本系统仅用于学习和研究

## 🔍 调试和日志

系统日志保存在 `logs/trading_system.log`，包含：

- 数据获取过程
- 技术指标计算
- 信号生成
- 订单执行
- 错误和警告

查看最新日志：

```bash
tail -f logs/trading_system.log
```

## 📚 参考资源

- [Alpaca API 文档](https://alpaca.markets/docs/api-references/)
- [yfinance 文档](https://github.com/ranaroussi/yfinance)
- [pandas-ta 文档](https://github.com/twopirllc/pandas-ta)
- [Telegram Bot API](https://core.telegram.org/bots/api)

## 📝 许可证

MIT License

## ✉️ 支持

如有问题或建议，欢迎反馈！

---

**最后更新**: 2024年5月

**注意**: 本系统仅供学习和研究使用。使用者自行承担所有风险和责任。
