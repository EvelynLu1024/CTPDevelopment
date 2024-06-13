import os
import threading  # 导入线程模块
import time  # 导入时间模块
import logging  # 导入 logging 模块
from datetime import datetime  # 导入日期时间模块
from login_cpi import MdSpiImpl  # 从 answer1_login_cpi 导入 MdSpiImpl 类
from config import get_product_id, get_trading_sessions, get_mainproduct_id  # 从 config.py 导入 get_product_id 和 get_trading_sessions 函数

# %% 设置工作目录
current_file_path = os.path.abspath(__file__)  # 获取当前脚本的绝对路径
current_dir = os.path.dirname(current_file_path)  # 获取当前脚本所在目录
os.chdir(current_dir)  # 设置当前脚本路径为工作目录

# 设置 logging 配置
log_dir = os.path.join(current_dir, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=os.path.join(log_dir, 'subscribe.log'), filemode='a')

class CustomMdSpi(MdSpiImpl):
    """自定义行情 SPI 类，继承自 MdSpiImpl。

    Attributes:
        instruments (list): 合约列表。
        product_id (str): 产品ID。
        trading_sessions (list): 交易时间段列表。
    """

    def __init__(self, product_id, trading_sessions):
        """初始化 CustomMdSpi 类。

        Args:
            product_id (str): 产品ID。
            trading_sessions (list): 交易时间段列表。
        """
        super().__init__()
        self.instruments = []  # 初始化合约列表
        self.product_id = product_id  # 保存产品ID
        self.trading_sessions = trading_sessions  # 保存交易时间段

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """用户登录响应"""
        super().OnRspUserLogin(pRspUserLogin, pRspInfo, nRequestID, bIsLast)
        if pRspInfo is not None and pRspInfo.ErrorID != 0:
            print(f"行情API登录失败. {pRspInfo.ErrorMsg}")
            logging.error(f"行情API登录失败. {pRspInfo.ErrorMsg}")
            return
        print("行情API登录成功.")
        logging.info("行情API登录成功。")
        # 订阅合约数据
        self.SubscribeMarketData([self.product_id])

    def OnRtnDepthMarketData(self, pDepthMarketData):
        """逐笔行情数据回报。
        当接收到逐笔行情数据时调用此方法。
        Args:
            pDepthMarketData: 深度行情数据。
        """
        print(f"接收到行情数据: {pDepthMarketData}")
        logging.info(f"接收到行情数据: {pDepthMarketData}")
        current_time = datetime.now().time()  # 获取当前时间

        # 检查当前时间是否在交易时间段内
        if not any(session[0] <= current_time <= session[1] for session in self.trading_sessions):
            return  # 非交易时间，忽略数据

        print(f"买一价: {pDepthMarketData.BidPrice1}, 最新价: {pDepthMarketData.LastPrice}, 卖一价: {pDepthMarketData.AskPrice1}, 成交量: {pDepthMarketData.Volume}")
        logging.info(f"买一价: {pDepthMarketData.BidPrice1}, 最新价: {pDepthMarketData.LastPrice}, 卖一价: {pDepthMarketData.AskPrice1}, 成交量: {pDepthMarketData.Volume}")
        # super().OnRtnDepthMarketData()

def main(product_name):
    """主程序。
    初始化自定义行情 SPI 实例，启动事件循环线程并查询合约。
    Args:
        product_name (str): 要查询的产品名称。
    """
    # 获取产品id
    product_id = get_product_id(product_name)  # 获取产品ID
    print(f"产品ID: {product_id}")
    logging.info(f"产品ID: {product_id}")
    if not product_id:
        print(f"未找到产品名称对应的ID: {product_name}")
        logging.error(f"未找到产品名称对应的ID: {product_name}")
        return

    # 获取交易时间段
    trading_sessions = get_trading_sessions(product_id)  # 获取产品的交易时间段
    print(f"交易时间段: {trading_sessions}")
    logging.info(f"交易时间段: {trading_sessions}")
    if not trading_sessions:
        print(f"未找到产品ID对应的交易时间段: {product_id}")
        logging.error(f"未找到产品ID对应的交易时间段: {product_id}")
        return

    # 计算主力合约
    product_id = get_mainproduct_id(product_id) # 此处应该接入一个主力合约计算函数

    md_spi = CustomMdSpi(product_id, trading_sessions)  # 创建自定义行情 SPI 实例，传入产品ID和交易时间段
    md_spi.initialize()  # 初始化行情 API

    # 启动行情 API 事件循环的线程
    md_thread = threading.Thread(target=md_spi.api.Join)
    md_thread.start()

    try:
        while md_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("停止行情订阅")
        logging.info("停止行情订阅")
        md_spi.api.Release()  # 释放 API

if __name__ == "__main__":
    product_name = "螺纹钢"  # 定义要查询的产品名称
    main(product_name)  # 调用主函数并传入产品名称
