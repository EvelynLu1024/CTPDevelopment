# CTP Python开发说明

### 概述：

### 资料
- SimNow官网：[上海期货交易所仿真模拟系统](https://www.simnow.com.cn/ "simnow官网")
- SimNow官方说明文件：[CTP客户端开发指南v3.5](./doc/CTP客户端开发指南 V3.5-中文.pdf "官方教程")
- CTP-API获取：[上海期货信息技术公司CTP-API下载（推荐）](http://www.sfit.com.cn/5_2_DocumentDown_2.htm "SFIT官网下载链接")或 [SimNow官网的CTP-API下载](https://www.simnow.com.cn/static/apiDownload.action "CTP-API 下载")

### 文件清单及用途说明

| 目录或脚本名称                                   | 用途说明                                                   |
|-------------------------------------------|--------------------------------------------------------|
| readme.md                                 | 项目的自述文件，介绍项目的功能和使用方法                                   |
| [SimNowID.yaml](#jump_sim)                | 基础配置，记录服务器地址、账户信息、交易所产品代码等基础信息                         |
| [config.py](#jump_con)                    | 配置文件，是基础配置与项目文件的对接函数                                   |
| [login_cpi.py](#jump_a1)          | 实现登录功能，连接交易平台                                          |
| [subscribe_rb.py](#jump_a2)       | 订阅市场数据模块，获取行情信息                                        |
| [query_position.py](#jump_a3)     | 查询持仓信息模块，获取账户的持仓数据                                     |
| [quant_trade.py](#jump_a4)        | 交易模块，实现交易策略和执行                                         |
| [traderapi672python38](#jump_headpackage) | 将CTP提供的C++接口打包成Python接口的项目文件                           |
| doc                                       | 存储项目相关的文档和说明文件                                         |
|                                           | CTP客户端开发指南 V3.5-中文.pdf                                 |
| image                                     | 存储项目相关的图片文件                                            |
|                                           | 下文提到，图1-5                                              |
| logs                                      | 存储项目运行时生成的日志文件                                         |
| venv                                      | 存储Python虚拟环境相关文件                                       |

### 操作流程
- <span id="jump_headpackage">**将C++头文件封装成python库** </span>：SimNow API为C++版本的头文件，Python编程需要通过SWIG将C++头文件编译成Python库，详细操作流程见[附录1](#jump_appendix1)。


- <span id="jump_sim">**SimNowID.yaml** </span>: 存储基础配置信息，包括SimNowID提供的接口地址、账户的基本信息、上交所产品代码等，方便在项目中调用，增加项目的可复用性和兼容性。</span><span id="jump_con">config.py文件作为基础配置与项目文件的对接函数，整理基础信息并导入。</span>


- <span id="jump_a1">**login_cpi** </span>: 配置交易/行情地址和接口，实现仿真账户登录验证。

  1.定义类MdSpiImpl：继承于CThostFtdcMdSpi，用于初始化行情API。用于行情登录和行情信息的订阅。

  2.定义类TdSpiImpl：继承于CThostFtdcTraderSpi，用于初始化交易API。使其能够持续接收和处理交易相关的事件

  3.导入logging模块，实时记录项目中的信息。

  4.作为后续功能登录行情和交易接口的父类。


- <span id="jump_a2">**subscribe_rb** </span>: 订阅螺纹钢期货当前主力合约行情，逐笔tick打印出买一价、最新价、卖一价、成交量。

  1. 定义类CustomMdSpi：继承自 MdSpiImpl，给出合约名称如“螺纹钢”，可根据SimNowID.yaml中的对应信息查询产品id，通过OnRspQryInstrument函数查询产品id对应的主力合约（月份），并订阅。

  2. 类函数OnRtnDepthMarketData查询并逐笔打印买一价、最新价、卖一价、成交量。

  3. 通过交易时间trading_sessions规避收到非交易时间行情。
     
     非交易时段有时也能接收到行情，原因是：日盘盘前可能会收到行情，是因为CTP日盘起动时会重演夜盘的流水，所以有可能会将夜盘的行情再推送一遍。日盘结束后也会收到行情，这是交易所结算完成发出的行情，这里面的结算价字段是当日结算价，一般推送时间在3点~3点半。

     解决方案：SimNowID.yaml文件中存储各个产品的交易时间trading_sessions，通过交易时间筛选，避免错误行情。
  4. 获取主力合约月份，通过config.py中的get_mainproduct_id函数实现。这个函数目前没有完成，在get_main_contract_code.py中写了一部分，但是没有调试。 

    后续思路是，根据当前时间，向后推11个月，查询对应的日成交额，选取成交额最高的合约作为当日主力合约。一般不会用近月合约作为主力合约，所以自动删除当月（特殊情况特殊合约单独讨论）。


- <span id="jump_a3">**query_position** </span>: 查询当前账户持仓，并打印

  1.定义类CustomTdSpi：继承自TdSpiImpl，查询持仓。


- <span id="jump_a4">**quant_trade**: 按照订阅的行情，对螺纹钢主力期货合约执行买卖操作。

   1. 是否使用异步编程？多线程更好调试，适合CPU密集型运算。异步编程在处理I/O密集型任务时更加高效。

### 有待改进
- 可继续将查询到信息存入数据库：构建一个redis数据库，逐笔查询、打印并存储。
- 可将上述程序封装成exe，做可视化界面，实现订单的查询、打印。但可能没有必要。



### <span id="jump_appendix1">附录1：通过SWIG将SimNow-API C++头文件编译成python库</span>
- 安装SWIG
  1. 官网下载安装包（下述window X64系统）：[SWIG安装包](https://swig.org/download.html "SWIG安装包下载")
  2. 安装步骤:
      1) 将swig安装包解压后添加至Path环境变量,如[图1](./image/pic_Path_SwigExe.png)；
      2) 将安装教程中提示的python_bin和python_lib路径添加至系统变量，如[图2](./image/pic_PathPython.png)；
      3) 检查安装：```cmd swig -version```，如[图3](./image/pic_Cmc_SwigVersion.png)。
- 操作过程

  **步骤一**. 通过SWIG生成C++的包装文件：

     ```> swig -python -c++ thosttraderapi.i```
   
    生成文件：1）thosttraderapi_wrap.cxx，thostmduserapi_wrap.cxx包含了将 ThostFtdcTraderApi，ThostFtdcMdApi 包装成 Python 模块的 C++ 代码。 2）thosttraderapi.py,thostmduserapi.py是SWIG 生成的 Python 文件，提供 Python 接口。

- **常见问题**
  
   问题1：
   
   ```>cmd > swig -python -c++ Thostmduserapi.i```时报警告
   
   ```ThostFtdcMdApi.h(30) : Warning 514: Director base class CThostFtdcMdSpi has no virtual destructor.```
   
   解决方案：

   在ThostFtdcMdApi.h的文件中添加```virtual ~CThostFtdcMdSpi() {} // 添加虚析构函数``,如[图5](./image/ThostFtdcMdApi.h增添虚构函数.png)。 不会对程序造成干扰，原因见[图6](./image/添加虚构函数的作用.png)。

   注：ThostFtdcTraderApi.h文件遇到相同问题，在文件中添加```virtual ~cThostFtdcTraderspi(){}//添加虚析构函数```

### 附录2：一些关于CTP库的关键信息或函数

   1. **CTP接口函数的命名规则**

| 消息            | 格式         | 示例                |
|-----------------|--------------|---------------------|
| 请求            | Req-----     | ReqUserLogin        |
| 响应            | OnRsp-----   | OnRspUserLogin      |
| 查询            | ReqQry-----  | ReqQryInstrument    |
| 查询请求的响应  | OnRspQry-----| OnRspQryInstrument  |
| 回报            | OnRtn-----   | OnRtnOrder          |
| 错误回报        | OnErrRtn-----| OnErrRtnOrderInsert |

### 贡献

欢迎任何形式的贡献！

贡献内容

1. **报告问题**: 如果你发现了任何错误或者有任何建议，请通过[EvelynLu1024@outlook.com](EvelynLu1024@outlook.com)联系。
2. **提交请求**: 如果你已经解决了一个问题或者添加了一个新功能，请提交一个Pull Request。
3. **改进文档**: 如果你发现文档有需要改进的地方，请随时提出或者直接修改并提交。

代码规范

- 确保代码风格与项目保持一致。
- 提交前请运行所有测试并确保它们都通过。

联系作者

- 如果你有任何问题或需要帮助，请联系 [EvelynLu1024@outlook.com](EvelynLu1024@outlook.com)。

感谢你的贡献！

### 许可证

MIT License

Copyright (c) [2024] [YingLu]
