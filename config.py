import yaml
from datetime import time as dtime

environment = "first_set"
group = 'dianxin1'  # 您可以"first_set"选择'dianxin1', 'dianxin2' 或 'yidong'，根据需要调整
config_yaml = "SimNowID.yaml"

# environment = "second_set"
# group = 'alltime'  # 您可以"first_set"选择'dianxin1', 'dianxin2' 或 'yidong'，根据需要调整
# config_yaml = "SimNowID.yaml"

def load_config(environment, group, file_path):
    """

    Args:
        environment: 对应SimNowID中的“first_set"或”second_set"
        group: "对应SimNowID中的'group1', 'group2' 或 'group3'或“alltime”
        file_path: "SimNowID.yaml"

    Returns:

    """
    with open(file_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    market_data_address = config['servers'][environment][group]['market_data_address']
    trading_address = config['servers'][environment][group]['trading_address']
    broker_id = config['account']['broker_id']
    user_id = config['account']['user_id']
    password = config['account']['password']
    investor_id = config['account']['investor_id']
    app_id = config['account']['app_id']
    auth_code = config['account']['auth_code']

    return market_data_address, trading_address, broker_id, user_id, password, investor_id, app_id, auth_code


MARKET_DATA_ADDRESS, TRADING_ADDRESS, BROKER_ID, USER_ID, PASSWORD, INVESTOR_ID, APP_ID, AUTH_CODE = load_config(environment, group, config_yaml)

def get_product_id(product_name, yaml_file='SimNowID.yaml'):
    """根据产品名称获取产品ID。

    Args:
        product_name (str): 产品名称。
        yaml_file (str): YAML 文件路径。

    Returns:
        str: 产品ID，如果找不到则返回 None。
    """
    with open(yaml_file, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    product_ids = data['products']
    return product_ids.get(product_name)

def get_mainproduct_id(product_id):
    """此处待补充一个求主力合约代码的函数"""
    return product_id + "2410"

def get_trading_sessions(product_id, yaml_file='SimNowID.yaml'):
    """根据产品ID获取交易时间段。

    Args:
        product_id (str): 产品ID。
        yaml_file (str): YAML 文件路径。

    Returns:
        list: 交易时间段的列表，每个时间段是一个包含四个元素的列表 [start_hour, start_minute, end_hour, end_minute]。
    """
    with open(yaml_file, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    sessions = data['trading_sessions']
    return [
        (dtime(start_hour, start_minute), dtime(end_hour, end_minute))
        for start_hour, start_minute, end_hour, end_minute in sessions.get(product_id, [])
    ]