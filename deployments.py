import json
import os
from network_config import networks  # Импортируем networks из файла network_config.py

# Получаем путь к папке, где находится скрипт
script_dir = os.path.dirname(os.path.realpath(__file__))

# Файл для хранения данных о контрактах, теперь в той же папке, что и скрипт
json_file = os.path.join(script_dir, 'deployments.json')


def load_deployments_data():
    """Загружает данные о контрактах из JSON файла"""
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}  # Если файл поврежден или пуст, возвращаем пустой словарь
    else:
        return {}


def save_deployments_data(data):
    """Сохраняет данные о контрактах в JSON файл"""
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

def check_network_limit(wallet_address, network_name):
    """Проверяет лимит контрактов на сети для кошелька"""
    data = load_deployments_data()
    
    if wallet_address not in data:
        data[wallet_address] = {}

    if network_name not in data[wallet_address]:
        data[wallet_address][network_name] = 0  # Если нет, то 0 контрактов на этой сети
    
    return data[wallet_address][network_name] < next(
        (net['limit'] for net in networks if net['name'] == network_name), 
        0
    )

def update_contract_count(wallet_address, network_name):
    """Обновляет количество контрактов для кошелька и сети"""
    data = load_deployments_data()
    
    if wallet_address not in data:
        data[wallet_address] = {}

    if network_name not in data[wallet_address]:
        data[wallet_address][network_name] = 0
    
    data[wallet_address][network_name] += 1
    save_deployments_data(data)
