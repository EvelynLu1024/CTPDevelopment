import os
import threading
import time
from datetime import datetime
from thostmduserapi import CThostFtdcMdApi, CThostFtdcMdSpi, CThostFtdcReqUserLoginField
from thosttraderapi import CThostFtdcTraderApi, CThostFtdcTraderSpi, CThostFtdcReqAuthenticateField, CThostFtdcReqUserLoginField, CThostFtdcInputOrderField, CThostFtdcOrderActionField
from config import get_product_id, get_trading_sessions, get_mainproduct_id, MARKET_DATA_ADDRESS, TRADING_ADDRESS, BROKER_ID, USER_ID, PASSWORD, INVESTOR_ID, APP_ID, AUTH_CODE
import logging

# 设置工作目录
current_file_path = os.path.abspath(__file__)  # 获取当前文件路径
current_dir = os.path.dirname(current_file_path)  # 获取当前文件目录
os.chdir(current_dir)  # 切换工作目录

# 创建日志目录
log_dir = os.path.join(current_dir, 'logs')  # 设置日志目录
if not os.path.exists(log_dir):
    os.makedirs(log_dir)  # 创建日志目录

# 创建独立的 logger
md_logger = logging.getLogger('market_data_logger')  # 创建一个名为'market_data_logger'的logger对象
md_logger.setLevel(logging.INFO)  # 设置日志级别为INFO及以上
md_handler = logging.FileHandler(os.path.join(log_dir, 'cpt_trade.log'))  # 创建一个文件处理器，用于存储日志信息
md_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')  # 设置日志格式，包括时间、日志级别和消息内容
md_handler.setFormatter(md_formatter)  # 将日志格式应用到文件处理器上
md_logger.addHandler(md_handler)  # 将文件处理器添加到logger对象中，以便将日志信息输出到文件中


class MarketDataSpi(CThostFtdcMdSpi):
    def __init__(self, md_api, auto_trade):
        """初始化MarketDataSpi类

        Args:
            md_api (CThostFtdcMdApi): 行情API实例
            auto_trade (AutoTradeSpi): 自动交易实例
        """
        super().__init__()
        self.md_api = md_api  # 行情API实例
        self.auto_trade = auto_trade  # 自动交易实例

    def OnFrontConnected(self):
        """行情API连接成功的回调函数"""
        print("行情API连接成功")
        md_logger.info("行情API连接成功")
        self.UserLogin()

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """用户登录响应处理函数

        Args:
            pRspUserLogin: 登录响应信息
            pRspInfo: 响应信息
            nRequestID: 请求ID
            bIsLast: 是否最后一条响应
        """
        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            print(f"行情API登录失败: {pRspInfo.ErrorMsg}")
            md_logger.error(f"行情API登录失败: {pRspInfo.ErrorMsg}")
            return
        print("行情API登录成功")
        md_logger.info("行情API登录成功")
        self.md_api.SubscribeMarketData([self.auto_trade.main_contract.encode('utf-8')], 1)

    def OnRtnDepthMarketData(self, pDepthMarketData):
        """逐笔行情数据返回时调用

        Args:
            pDepthMarketData: 深度行情数据
        """
        print(f"接收到行情数据: {pDepthMarketData}")
        md_logger.info(f"接收到行情数据: {pDepthMarketData}")
        current_time = datetime.now().time()  # 获取当前时间
        # 检查当前时间是否在交易时间段内
        if not any(session[0] <= current_time <= session[1] for session in self.auto_trade.trading_sessions):
            return  # 非交易时间，忽略数据

        print(f"买一价: {pDepthMarketData.BidPrice1}, 最新价: {pDepthMarketData.LastPrice}, 卖一价: {pDepthMarketData.AskPrice1}, 成交量: {pDepthMarketData.Volume}")
        logging.info(f"买一价: {pDepthMarketData.BidPrice1}, 最新价: {pDepthMarketData.LastPrice}, 卖一价: {pDepthMarketData.AskPrice1}, 成交量: {pDepthMarketData.Volume}")

        self.auto_trade.on_market_data(pDepthMarketData)

    def UserLogin(self):
        """用户登录"""
        login_field = CThostFtdcReqUserLoginField()
        login_field.BrokerID = BROKER_ID
        login_field.UserID = USER_ID
        login_field.Password = PASSWORD
        self.md_api.ReqUserLogin(login_field, 0)


class TraderSpi(CThostFtdcTraderSpi):
    def __init__(self, td_api, auto_trade):
        """初始化TraderSpi类

        Args:
            td_api (CThostFtdcTraderApi): 交易API实例
            auto_trade (AutoTradeSpi): 自动交易实例
        """
        super().__init__()
        self.td_api = td_api  # 交易API实例
        self.auto_trade = auto_trade  # 自动交易实例

    def OnFrontConnected(self):
        """交易API连接成功的回调函数"""
        print("交易API连接成功")
        md_logger.info("交易API连接成功")
        self.ReqAuthenticate()

    def OnRspAuthenticate(self, pRspAuthenticateField, pRspInfo, nRequestID, bIsLast):
        """认证响应处理函数

        Args:
            pRspAuthenticateField: 认证响应信息
            pRspInfo: 响应信息
            nRequestID: 请求ID
            bIsLast: 是否最后一条响应
        """
        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            print(f"交易API认证失败: {pRspInfo.ErrorMsg}")
            md_logger.error(f"交易API认证失败: {pRspInfo.ErrorMsg}")
            return
        print("交易API认证成功")
        md_logger.info("交易API认证成功")
        self.UserLogin()

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """用户登录响应处理函数

        Args:
            pRspUserLogin: 登录响应信息
            pRspInfo: 响应信息
            nRequestID: 请求ID
            bIsLast: 是否最后一条响应
        """
        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            print(f"交易API登录失败: {pRspInfo.ErrorMsg}")
            md_logger.error(f"交易API登录失败: {pRspInfo.ErrorMsg}")
            return
        print("交易API登录成功")
        md_logger.info("交易API登录成功")
        # 在这里可以进行进一步操作

    def OnRtnOrder(self, pOrder):
        """报单回调函数

        Args:
            pOrder: 报单信息
        """
        if pOrder.OrderStatus == '0':  # 订单已成交
            print(f"订单成交: {pOrder.OrderSysID}")
            md_logger.info(f"订单成交: {pOrder.OrderSysID}")
            self.auto_trade.unfilled_orders.pop(pOrder.OrderRef, None)
            self.auto_trade.pending_order = False

        # 保存订单系统ID和交易所ID，用于撤销订单
        self.auto_trade.order_info[pOrder.OrderRef] = (pOrder.OrderSysID, pOrder.ExchangeID)

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        """订单录入响应

        Args:
            pInputOrder: 订单信息
            pRspInfo: 响应信息
            nRequestID: 请求ID
            bIsLast: 是否最后一条响应
        """
        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            print(f"订单录入失败: {pRspInfo.ErrorMsg}")
            md_logger.error(f"订单录入失败: {pRspInfo.ErrorMsg}")
            self.auto_trade.pending_order = False
            return
        print(f"订单录入成功: {pInputOrder.OrderRef}")
        md_logger.info(f"订单录入成功: {pInputOrder.OrderRef}")

    def ReqAuthenticate(self):
        """请求认证"""
        auth_field = CThostFtdcReqAuthenticateField()
        auth_field.BrokerID = BROKER_ID
        auth_field.UserID = USER_ID
        auth_field.AuthCode = AUTH_CODE
        auth_field.AppID = APP_ID
        self.td_api.ReqAuthenticate(auth_field, 0)

    def UserLogin(self):
        """用户登录"""
        login_field = CThostFtdcReqUserLoginField()
        login_field.BrokerID = BROKER_ID
        login_field.UserID = USER_ID
        login_field.Password = PASSWORD
        self.td_api.ReqUserLogin(login_field, 0)


class AutoTradeSpi:
    def __init__(self, product_name):
        """初始化AutoTradeSpi类

        Args:
            product_name (str): 产品名称
        """
        self.main_contract = get_product_id(product_name)  # 获取产品ID
        self.main_contract = get_mainproduct_id(self.main_contract)  # 获取主力合约ID
        self.md_api = CThostFtdcMdApi.CreateFtdcMdApi()  # 创建行情API实例
        self.td_api = CThostFtdcTraderApi.CreateFtdcTraderApi()  # 创建交易API实例
        self.md_spi = MarketDataSpi(self.md_api, self)  # 创建行情SPI实例
        self.td_spi = TraderSpi(self.td_api, self)  # 创建交易SPI实例
        self.current_position = 0  # 当前持仓
        self.pending_order = False  # 待成交订单状态
        self.last_tick_time = None  # 上一个tick时间
        self.last_tick_price = None  # 上一个tick价格
        self.unfilled_orders = {}  # 未成交订单
        self.order_info = {}  # 存储订单的系统ID和交易所ID
        self.last_2_ticks = []  # 最近2个tick的价格
        self.trading_sessions = get_trading_sessions(get_product_id(product_name))  # 获取交易时间段
        self.next_order = None  # 下一个订单信息

    def initialize(self):
        """初始化行情和交易SPI"""
        self.initialize_md()
        self.initialize_td()

    def initialize_md(self):
        """初始化行情SPI"""
        self.md_api.RegisterFront(MARKET_DATA_ADDRESS)  # 注册行情前置地址
        self.md_api.RegisterSpi(self.md_spi)  # 注册行情SPI
        self.md_api.Init()  # 初始化行情API

    def initialize_td(self):
        """初始化交易SPI"""
        self.td_api.RegisterFront(TRADING_ADDRESS)  # 注册交易前置地址
        self.td_api.RegisterSpi(self.td_spi)  # 注册交易SPI
        self.td_api.SubscribePublicTopic(0)  # 订阅公有流
        self.td_api.SubscribePrivateTopic(0)  # 订阅私有流
        self.td_api.Init()  # 初始化交易API

    def on_market_data(self, pDepthMarketData):
        """处理市场数据

        Args:
            pDepthMarketData: 深度行情数据
        """
        current_time = datetime.now()
        if self.last_tick_time and (current_time - self.last_tick_time).seconds >= 20:
            self.CancelAllOrders()  # 撤销所有订单

        if self.pending_order:  # 如果有待成交的订单，则不操作
            return

        # 更新最近两个tick的价格
        self.last_2_ticks.append(pDepthMarketData.LastPrice)
        if len(self.last_2_ticks) > 2:
            self.last_2_ticks.pop(0)

        # 如果存在下一个订单信息且当前持仓为0
        if self.next_order and self.current_position == 0:
            if self.next_order['direction'] == 'sell':
                self.PlaceOrder(pDepthMarketData.AskPrice1, 'sell')
            elif self.next_order['direction'] == 'buy':
                self.PlaceOrder(pDepthMarketData.BidPrice1, 'buy')
            self.next_order = None  # 清除下一个订单信息
            return

        if self.current_position == 0:
            if len(self.last_2_ticks) == 2:
                # 判断最近连续2个tick的成交价
                if self.last_2_ticks[0] >= pDepthMarketData.AskPrice1 and self.last_2_ticks[1] >= pDepthMarketData.AskPrice1:
                    self.next_order = {'direction': 'sell'}
                elif self.last_2_ticks[0] <= pDepthMarketData.BidPrice1 and self.last_2_ticks[1] <= pDepthMarketData.BidPrice1:
                    self.next_order = {'direction': 'buy'}
        else:
            # 平仓逻辑
            if self.current_position > 0:
                self.PlaceOrder(pDepthMarketData.BidPrice1, 'sell_close')
            elif self.current_position < 0:
                self.PlaceOrder(pDepthMarketData.AskPrice1, 'buy_close')

        self.last_tick_time = current_time
        self.last_tick_price = pDepthMarketData.LastPrice

    def PlaceOrder(self, price, direction):
        """下单函数

        Args:
            price (float): 订单价格
            direction (str): 交易方向 ('buy', 'sell', 'buy_close', 'sell_close')
        """
        order = CThostFtdcInputOrderField()  # 创建订单对象
        order.BrokerID = BROKER_ID
        order.InvestorID = INVESTOR_ID
        order.InstrumentID = self.main_contract
        order.LimitPrice = price
        order.VolumeTotalOriginal = 1
        order.OrderPriceType = '2'
        order.Direction = '0' if direction == 'buy' else '1'
        order.CombOffsetFlag = '0' if direction in ['buy', 'sell'] else '1'
        order.CombHedgeFlag = '1'
        order.ContingentCondition = '1'
        order.ForceCloseReason = '0'
        order.IsAutoSuspend = 0
        order.TimeCondition = '3'
        order.VolumeCondition = '1'
        order.MinVolume = 1
        order.StopPrice = 0
        order.RequestID = 0
        order.UserForceClose = 0

        self.td_api.ReqOrderInsert(order, 0)
        self.pending_order = True
        self.unfilled_orders[order.OrderRef] = datetime.now()

    def CancelAllOrders(self):
        """撤销所有未成交订单"""
        for order_ref, order_time in list(self.unfilled_orders.items()):
            if (datetime.now() - order_time).seconds >= 20:
                if order_ref in self.order_info:
                    cancel_order = CThostFtdcOrderActionField()
                    cancel_order.BrokerID = BROKER_ID
                    cancel_order.InvestorID = INVESTOR_ID
                    cancel_order.UserID = INVESTOR_ID
                    cancel_order.OrderRef = order_ref
                    cancel_order.ActionFlag = '0'

                    # 获取 OrderSysID 和 ExchangeID
                    cancel_order.OrderSysID, cancel_order.ExchangeID = self.order_info[order_ref]

                    self.td_api.ReqOrderAction(cancel_order, 0)
                    self.unfilled_orders.pop(order_ref)
                    self.pending_order = False

def main(product_name):
    """主函数

    Args:
        product_name (str): 产品名称
    """
    auto_trade_spi = AutoTradeSpi(product_name)  # 创建AutoTradeSpi实例
    auto_trade_spi.initialize()  # 初始化

    md_thread = threading.Thread(target=auto_trade_spi.md_api.Join)  # 启动行情API事件循环
    td_thread = threading.Thread(target=auto_trade_spi.td_api.Join)  # 启动交易API事件循环

    md_thread.start()  # 启动行情API线程
    td_thread.start()  # 启动交易API线程

    try:
        while md_thread.is_alive() and td_thread.is_alive():  # 检查线程是否仍在运行
            time.sleep(1)  # 等待一秒钟
    except KeyboardInterrupt:
        print("停止自动交易")  # 打印停止消息
        auto_trade_spi.md_api.Release()  # 释放行情API资源
        auto_trade_spi.td_api.Release()  # 释放交易API资源

if __name__ == "__main__":
    main("螺纹钢")  # 调用主函数并传入产品名称
