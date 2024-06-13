import os
import threading
import time
import logging
from datetime import datetime
from login_cpi import TdSpiImpl
from thosttraderapi import CThostFtdcQryInvestorPositionField
from config import TRADING_ADDRESS, BROKER_ID, USER_ID, PASSWORD, INVESTOR_ID

# 设置 logging 配置
log_dir = os.path.join(os.getcwd(), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=os.path.join(log_dir, 'query_position.log'), filemode='a')

class CustomTdSpi(TdSpiImpl):
    """自定义交易SPI类，继承自TdSpiImpl"""

    def __init__(self, query_event):
        super().__init__()  # 调用父类的初始化方法
        self.positions = []  # 初始化一个空列表用于存储持仓信息
        self.query_event = query_event  # 事件对象，用于协调查询操作

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """用户登录响应"""
        if pRspInfo is not None and pRspInfo.ErrorID != 0:  # 如果响应信息不为空且存在错误
            print(f"登录失败. {pRspInfo.ErrorMsg}")  # 打印错误消息
            logging.error(f"登录失败. {pRspInfo.ErrorMsg}")
            return  # 返回，停止后续执行
        print(f"登录成功. {pRspUserLogin.TradingDay}")  # 打印登录成功消息和交易日
        logging.info(f"登录成功. {pRspUserLogin.TradingDay}")
        self.QueryPosition()  # 调用查询持仓方法

    def OnRspQryInvestorPosition(self, pInvestorPosition, pRspInfo, nRequestID, bIsLast):
        """查询持仓响应"""
        if pRspInfo is not None and pRspInfo.ErrorID != 0:  # 如果响应信息不为空且存在错误
            print(f"查询持仓失败. {pRspInfo.ErrorMsg}")  # 打印错误消息
            logging.error(f"查询持仓失败. {pRspInfo.ErrorMsg}")
            return  # 返回，停止后续执行
        if pInvestorPosition is not None:  # 如果持仓信息不为空
            print(f"收到持仓信息: {pInvestorPosition.InstrumentID}, 持仓量: {pInvestorPosition.Position}")
            logging.info(f"收到持仓信息: {pInvestorPosition.InstrumentID}, 持仓量: {pInvestorPosition.Position}")
            self.positions.append(pInvestorPosition)  # 将持仓信息添加到列表中
        else:
            print("没有收到持仓信息")
            logging.info("没有收到持仓信息")
        if bIsLast:  # 如果这是最后一条响应
            self.PrintPositions()  # 打印所有持仓信息
            self.query_event.set()  # 设置事件，表示查询已完成
        # super().OnRspQryInvestorPosition()

    def QueryPosition(self):
        """查询持仓"""
        print("发送持仓查询请求")
        logging.info("发送持仓查询请求")
        req = CThostFtdcQryInvestorPositionField()  # 创建查询持仓请求对象
        req.BrokerID = BROKER_ID  # 设置经纪公司ID
        req.InvestorID = INVESTOR_ID  # 设置投资者ID
        self.api.ReqQryInvestorPosition(req, 0)  # 发送查询请求

    def PrintPositions(self):
        """打印持仓信息"""
        if not self.positions:
            print("当前没有持仓")
            logging.info("当前没有持仓")
        for pos in self.positions:  # 遍历所有持仓信息
            direction = '多头' if pos.PosiDirection == '2' else '空头'  # 根据持仓方向设置文字
            print(
                f"合约代码: {pos.InstrumentID}, 持仓量: {pos.Position}, 多空方向: {direction}, 持仓成本: {pos.PositionCost}")  # 打印持仓信息
            logging.info(
                f"合约代码: {pos.InstrumentID}, 持仓量: {pos.Position}, 多空方向: {direction}, 持仓成本: {pos.PositionCost}")

def main():
    query_event = threading.Event()  # 创建事件对象
    td_spi = CustomTdSpi(query_event)  # 创建自定义交易SPI实例，传入事件对象
    td_spi.initialize()  # 初始化交易API

    td_thread = threading.Thread(target=td_spi.api.Join)  # 创建并启动交易API事件循环线程
    td_thread.start()  # 启动线程

    try:  # 如果没有查到，就每秒钟查一次，查到就不再查了
        while not query_event.is_set():  # 等待查询事件完成
            time.sleep(1)  # 每秒钟检查一次
    except KeyboardInterrupt:  # 如果用户按下Ctrl+C
        print("停止持仓查询")  # 打印停止消息
        logging.info("停止持仓查询")
        td_spi.api.Release()  # 释放API资源



if __name__ == "__main__":
    main()  # 执行main函数
