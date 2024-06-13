import os
import logging  # 导入 logging 模块
from thostmduserapi import CThostFtdcMdApi, CThostFtdcMdSpi, CThostFtdcReqUserLoginField
from thosttraderapi import CThostFtdcTraderApi, CThostFtdcTraderSpi, CThostFtdcReqAuthenticateField, \
    CThostFtdcReqUserLoginField
from config import MARKET_DATA_ADDRESS, TRADING_ADDRESS, BROKER_ID, USER_ID, PASSWORD, INVESTOR_ID, APP_ID, AUTH_CODE

# %% 设置工作目录
current_file_path = os.path.abspath(__file__)  # 获取当前脚本的绝对路径
current_dir = os.path.dirname(current_file_path)  # 获取当前脚本所在目录
os.chdir(current_dir)  # 设置当前脚本路径为工作目录

# 创建独立的 logger
md_logger = logging.getLogger('market_data_logger')
md_logger.setLevel(logging.INFO)
md_handler = logging.FileHandler('logs/cpi_login_md.log')
md_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
md_handler.setFormatter(md_formatter)
md_logger.addHandler(md_handler)

td_logger = logging.getLogger('trading_data_logger')
td_logger.setLevel(logging.INFO)
td_handler = logging.FileHandler('logs/cpi_login_td.log')
td_handler.setFormatter(md_formatter)
td_logger.addHandler(td_handler)


class MdSpiImpl(CThostFtdcMdSpi):
    """行情API"""

    def __init__(self, log_path="logs"):
        super().__init__()
        self.api = None  # 声明类中要用的变量：api变量
        self.log_path = log_path  # 日志文件夹路径

    def initialize(self):
        md_log_path = os.path.join(self.log_path, "market_data")  # 行情日志文件夹
        if not os.path.exists(md_log_path):
            os.makedirs(md_log_path)  # 创建行情日志文件夹
        flow_path = os.path.join(md_log_path, "flow_logs", USER_ID)
        if not os.path.exists(flow_path):
            os.makedirs(flow_path)  # 创建用户日志文件夹
        self.api = CThostFtdcMdApi.CreateFtdcMdApi(flow_path)  # 初始化API并指定日志文件夹路径
        self.api.RegisterFront(MARKET_DATA_ADDRESS)  # 注册行情前置地址
        self.api.RegisterSpi(self)  # 注册行情SPI
        self.api.Init()  # 初始化行情API

    def OnFrontConnected(self):
        """建立连接"""
        print("行情API连接成功。")
        md_logger.info("行情API连接成功。")
        self.UserLogin()  # 调用用户登录方法

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """用户登录响应"""
        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            print(f"行情API登录失败. {pRspInfo.ErrorMsg}")
            md_logger.error(f"行情API登录失败. {pRspInfo.ErrorMsg}")
            return
        print("行情API登录成功.")
        md_logger.info("行情API登录成功。")


    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        """错误响应"""
        print(f"错误响应, 错误代码: {pRspInfo.ErrorID}, 错误信息: {pRspInfo.ErrorMsg}")
        md_logger.error(f"错误响应, 错误代码: {pRspInfo.ErrorID}, 错误信息: {pRspInfo.ErrorMsg}")

    def UserLogin(self):
        req = CThostFtdcReqUserLoginField()  # 创建用户登录请求结构体
        req.BrokerID = BROKER_ID  # 设置经纪公司ID
        req.UserID = USER_ID  # 设置用户ID
        req.Password = PASSWORD  # 设置用户密码
        self.api.ReqUserLogin(req, 0)  # 发送登录请求

    def SubscribeMarketData(self, instruments_id):
        if self.api is None:
            raise RuntimeError("API is not initialized.")
        instruments = [x.encode('utf-8') for x in instruments_id]  # 定义要订阅的合约ID列表，并进行UTF-8编码
        self.api.SubscribeMarketData(instruments, len(instruments))  # 订阅行情数据



# 创建交易API实例
class TdSpiImpl(CThostFtdcTraderSpi):
    def __init__(self, log_path="logs"):
        super().__init__()
        self.api = None  # 声明API变量
        self.log_path = log_path  # 日志文件夹路径

    def initialize(self):
        td_log_path = os.path.join(self.log_path, "trading_data")  # 交易日志文件夹
        if not os.path.exists(td_log_path):
            os.makedirs(td_log_path)  # 创建交易日志文件夹
        flow_path = os.path.join(td_log_path, "flow_logs", USER_ID)
        if not os.path.exists(flow_path):
            os.makedirs(flow_path)  # 创建用户日志文件夹
        self.api = CThostFtdcTraderApi.CreateFtdcTraderApi(flow_path)  # 初始化交易API并传递日志文件夹路径
        # 注册交易前置地址和SPI
        self.api.RegisterFront(TRADING_ADDRESS)  # 注册交易前置地址
        self.api.RegisterSpi(self)  # 注册交易SPI
        self.api.SubscribePublicTopic(0)  # 订阅公有流
        self.api.SubscribePrivateTopic(0)  # 订阅私有流
        self.api.Init()  # 初始化交易API

    def OnFrontConnected(self):
        """ 建立连接
        客户端到交易前置的无身份验证连接建立之后，这个函数会被调用，用于说明连接已经建立。连接建立之后，才能请求认证。
        """
        print("交易API连接成功。")
        td_logger.info("交易API连接成功。")
        self.ReqAuthenticate()  # 调用认证方法
        # super().OnFrontConnected()  # 调用父类方法

    def OnRspAuthenticate(self, pRspAuthenticateField, pRspInfo, nRequestID, bIsLast):
        """ 认证响应
        Args:
            pRspAuthenticateField: 认证响应字段
            pRspInfo: 响应信息
            nRequestID: 请求ID
            bIsLast: 是否最后一条响应
        """
        if pRspInfo:
            print("认证响应", pRspInfo.ErrorID, pRspInfo.ErrorMsg)
        if pRspInfo and pRspInfo.ErrorID != 0:
            return
        if pRspInfo.ErrorID == 0:
            self.UserLogin()
        # super().OnRspAuthenticate(pRspAuthenticateField, pRspInfo, nRequestID, bIsLast)  # 调用父类方法

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """ 用户登录响应
        Args:
            pRspUserLogin: 用户登录响应字段
            pRspInfo: 响应信息
            nRequestID: 请求ID
            bIsLast: 是否最后一条响应
        """
        if pRspInfo:
            print("登录响应", pRspInfo.ErrorID, pRspInfo.ErrorMsg)
            td_logger.info(f"登录响应: {pRspInfo.ErrorID}, {pRspInfo.ErrorMsg}")
        # super().OnRspUserLogin(pRspUserLogin, pRspInfo, nRequestID, bIsLast)  # 调用父类方法

    def ReqAuthenticate(self):
        req = CThostFtdcReqAuthenticateField()  # 创建认证请求结构体
        req.BrokerID = BROKER_ID  # 设置经纪公司ID
        req.UserID = USER_ID  # 设置用户ID
        req.AppID = APP_ID  # 设置应用ID
        req.AuthCode = AUTH_CODE  # 设置认证码
        self.api.ReqAuthenticate(req, 0)  # 发送认证请求

    def UserLogin(self):
        req = CThostFtdcReqUserLoginField()  # 创建用户登录请求结构体
        req.BrokerID = BROKER_ID  # 设置经纪公司ID
        req.UserID = USER_ID  # 设置用户ID
        req.Password = PASSWORD  # 设置用户密码
        req.InvestorID = INVESTOR_ID  # 设置投资者ID
        self.api.ReqUserLogin(req, 0)  # 发送登录请求

if __name__ == "__main__":
    # ———————————— 运行行情API ————————————
    # 初始化并启动行情API
    md_spi = MdSpiImpl()  # 创建行情spi实例，实现一些虚函数
    md_spi.SubscribeMarketData([""])
    md_spi.initialize()

    # ———————————— 运行交易API ————————————
    # 初始化并启动交易API
    td_spi = TdSpiImpl()  # 创建交易SPI实例
    td_spi.initialize()

    # 启动事件循环
    md_spi.api.Join()  # 保持行情API的事件循环，使其能够持续接收和处理行情数据
    td_spi.api.Join()  # 保持交易API的事件循环，使其能够持续接收和处理交易相关的事件
