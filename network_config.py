import json
import random
import os

# Данные сетей с именами и лимитами
networks = [
    {
        "name": "Base",
        "chain_id": 8453,
        "rpc_url": "https://base-rpc.publicnode.com",
        "limit": 1,  # Лимит контрактов для этой сети
    },
    {
        "name": "Optimism",
        "chain_id": 10,
        "rpc_url": "https://optimism.llamarpc.com",
        "limit": 1,
    },
    {
        "name": "BOB",
        "chain_id": 60808,
        "rpc_url": "https://bob-mainnet.public.blastapi.io",
        "limit": 1,
    },
    {
        "name": "Ink",
        "chain_id": 57073,
        "rpc_url": "https://rpc-qnd.inkonchain.com",
        "limit": 10,
    },
    {
        "name": "Mode",
        "chain_id": 34443,
        "rpc_url": "https://1rpc.io/mode",
        "limit": 10,
    },
    {
        "name": "Blast",
        "chain_id": 81457,
        "rpc_url": "https://rpc.blast.io",
        "limit": 10,
    }
]

# Глобальные настройки задержки (от и до, в секундах)
delay_min = 2  # Минимальная задержка
delay_max = 5  # Максимальная задержка

# Файл для хранения данных о контрактах
json_file = 'deployments.json'


def load_deployments_data():
    """Загружает данные о контрактах из JSON файла"""
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_deployments_data(data):
    """Сохраняет данные о контрактах в JSON файл"""
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

def get_random_network():
    """Возвращает случайную сеть из списка"""
    return random.choice(networks)

def get_random_delay():
    """Возвращает случайную задержку в пределах диапазона"""
    return random.uniform(delay_min, delay_max)

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
