这是一份针对美股超短线量化交易系统的详细**概要设计文档（High-Level Design）**。本设计侧重于系统各模块的解耦、线程安全模型以及处理高频交易特性的核心逻辑。

# **量化交易系统概要设计文档 (HLD)**

## **1\. 系统架构图**

系统采用 **生产者-消费者 (Producer-Consumer)** 模型，通过内存无锁队列传递数据，确保交易核心模块与 GUI 界面完全解耦。

## **2\. 模块详细设计**

### **2.1 数据接入与预处理模块 (Data Ingestion Layer)**

* **连接器适配器 (Adaptor Pattern):** 为 Alpaca、Alpha Vantage 等构建统一接口。  
* **归一化引擎:** 将不同数据源的原始数据（JSON）解析并映射为内存中的标准 Bar 结构（Open, High, Low, Close, Volume, Timestamp）。  
* **数据缓存 (Ring Buffer):** 使用固定长度的环形队列存储最新 $N$ 个周期的数据，满足技术指标快速计算的需求。

### **2.2 策略核心引擎 (Strategy Kernel)**

* **逻辑解耦:** 策略类仅负责接收数据和产生决策，不直接触碰网络和 UI。  
* **事件触发机制:**  
  * onTick(): 实时波动处理（用于触发止损/止盈）。  
  * onBar(): 周期性策略执行（MACD/RSI 信号判定）。  
* **指标计算流水线:** 利用 xsimd 进行向量化处理，确保在一个 onBar() 周期内，几十个标的物（Ticker）的指标计算在微秒级完成。

### **2.3 执行与风控模块 (Execution & Risk Management)**

* **订单生命周期管理 (OMS):**  
  * 维护订单状态机（Pending \-\> Submitted \-\> Filled / Rejected / Cancelled）。  
  * 自动填充 Alpaca 要求的 ClientOrderID 用于跟踪。  
* **硬风控 (Pre-Trade Risk):**  
  * 单笔最大下单金额限制。  
  * 日内最大亏损熔断。  
  * 基于 ATR 的动态止损位计算。

### **2.4 GUI 显示层 (UI Presentation Layer)**

* **渲染循环:** Dear ImGui 通过 GLFW 或 SDL2 挂载，利用 GPU 硬件加速。  
* **异步刷新:** UI 线程通过 std::atomic 或 std::shared\_mutex 从策略层读取最新状态，避免锁竞争导致交易卡顿。

## **3\. 核心数据流设计 (Data Flow)**

1. **数据流向:** 网络 Socket \-\> Raw Parser \-\> Data Buffer \-\> Strategy Logic \-\> Order Manager \-\> REST/WS API。  
2. **状态同步:**  
   * 所有账户余额、仓位、订单状态均维护在全局 AccountManager 中。  
   * UI 层定期查询 AccountManager 以刷新账户资产净值。  
   * 交易发生时，通过异步消息机制推送至 UI 层进行更新。

## **4\. 关键技术支撑**

### **4.1 指标计算接口 (SIMD Vectorization)**

对于 MACD 等时序计算，避免逐点循环。通过批量加载数据到内存对齐的数组中，利用 CPU 的 AVX-512/AVX2 指令一次性处理 8-16 个点。

### **4.2 线程模型**

* **Thread 1 (Network Thread):** 负责维护 WebSocket 长连接，处理数据收发。  
* **Thread 2 (Strategy Thread):** 高优先级，负责策略逻辑和指标计算。  
* **Thread 3 (UI Thread):** 负责渲染界面，处理用户交互。  
* **Thread 4 (Logging & Alert):** 负责文件 IO 与 Telegram 告警。

## **5\. 系统容灾与可靠性策略**

* **断网自动撤单:** 监测到心跳丢失超过 $X$ 秒，立即向交易所发送 CancelAll 指令。  
* **状态持久化:** 所有订单请求和执行结果均采用 Append-only 的方式实时写入 SQLite 数据库。若系统崩溃，重启后通过 AccountManager 恢复现场，重新同步未完成订单。  
* **熔断保护:** 设定 Hard-Stop，当账户当日累计亏损达到预设阈值时，自动触发清仓并禁止进一步交易。

## **6\. 开发环境与依赖管理**

* **构建系统:** CMake (确保跨平台)。  
* **包管理:** vcpkg 或 Conan (用于管理 Boost, nlohmann-json, cpp-httplib, spdlog)。

### **设计总结**

该概要设计将系统划分为“数据接入”、“逻辑计算”、“执行管理”、“界面显示”四个独立维度。开发时，建议先完成 数据层 \-\> 策略层 的本地回测环境，然后再挂载 UI层 和 网络接口层。  
您是否需要针对其中的某一个模块（例如**交易策略接口定义**或**SIMD指标库封装**）深入讨论其代码实现细节？