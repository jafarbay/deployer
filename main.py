import time
from web3 import Web3
from solcx import compile_source, install_solc
import traceback
from network_config import get_random_network, get_random_delay, networks
from contracts import get_random_contract
from relay import bridge_eth  # Импортируем функцию бриджа
from deployments import check_network_limit, update_contract_count  # Импортируем функции для работы с JSON

# Устанавливаем нужную версию Solidity
install_solc('0.8.0')

# Чтение приватных ключей
def load_private_keys(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

private_keys = load_private_keys('privates.txt')

def get_balance(w3, address):
    return w3.eth.get_balance(address)

def find_max_balance_network(account_address):
    max_balance = 0
    best_network = None
    
    for network in networks:
        w3 = Web3(Web3.HTTPProvider(network['rpc_url']))
        if not w3.is_connected():
            print(f"Не удается подключиться к сети {network['name']}.")
            continue

        # Получаем баланс для сети
        balance = get_balance(w3, account_address)
        print(f"Баланс в сети {network['name']}: {balance}")  # Добавление отладки
        
        # Проверяем, является ли баланс максимальным
        if balance > max_balance:
            max_balance = balance
            best_network = network
    
    if best_network is not None:
        print(f"Сеть с максимальным балансом: {best_network['name']}, Баланс: {max_balance}")
    else:
        print("Не удалось найти сеть с максимальным балансом.")
    
    return best_network, max_balance

# Функция для записи логов в файл
def log_to_file(message):
    with open('deployments.log', 'a') as log_file:
        log_file.write(f"{message}\n")

# Развертывание контракта
for private_key in private_keys:
    try:
        account = Web3().eth.account.from_key(private_key)
        wallet_address = account.address
        print(f"\nProcessing wallet with address: {wallet_address}")

        contract_name, contract_source_code, constructor_args = get_random_contract()
        print(f"Selected contract: {contract_name}")

        compiled_sol = compile_source(contract_source_code, solc_version='0.8.0')
        contract_id, contract_interface = compiled_sol.popitem()
        abi = contract_interface['abi']
        bytecode = contract_interface['bin']

        # Выбираем сеть
        network = get_random_network()
        print(f"Selected network: {network['name']} ({network['chain_id']})")
        # Проверяем, не превышен ли лимит контрактов на сети для кошелька
        while not check_network_limit(wallet_address, network['name']):
            print(f"Limit exceeded on {network['name']}. Trying another network...")
            network = get_random_network()
            time.sleep(2)
            print(f"New network selected: {network['name']} ({network['chain_id']})")
        w3 = Web3(Web3.HTTPProvider(network['rpc_url']))

        if not w3.is_connected():
            print(f"Failed to connect to {network['name']} ({network['chain_id']})")
            continue

        balance = get_balance(w3, wallet_address)
        gas_price = w3.eth.gas_price
        contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        gas_estimate = contract.constructor(*constructor_args).estimate_gas({'from': wallet_address})
        needed_eth = gas_price * gas_estimate * 1.3

        if balance < needed_eth:
            print(f"Not enough ETH on {network['name']} ({network['chain_id']}). Need {needed_eth/10**18}, has {balance/10**18}")
            best_network, max_balance = find_max_balance_network(wallet_address)
            if best_network and max_balance > needed_eth:
                print(f"Bridging from {best_network['name']}  {(needed_eth * 20)/10**18} ({best_network['chain_id']}) to {network['name']} ({network['chain_id']})")
                bridge_eth(private_key, needed_eth * 20, best_network['chain_id'], network['chain_id'], {net['chain_id']: net['rpc_url'] for net in networks})

                # Ожидание пополнения баланса
                wait_time = 35  # интервал между проверками
                print(f"Starting to wait for balance update. Checking every {wait_time} seconds...")
                while True:
                    time.sleep(wait_time)  # Проверяем баланс каждые 10 секунд
                    balance = get_balance(w3, wallet_address)
                    print(f"Balance after bridging: {balance}")
                    if balance >= needed_eth:
                        print("Баланс пополнен, продолжаем отправку транзакции.")
                        break
                    else:
                        print("Баланс все еще недостаточен. Ожидаем...")

            else:
                print("No network with enough funds found. Skipping.")
                continue

        # Проверяем лимит контрактов перед развертыванием
        if check_network_limit(wallet_address, network['name']):
            nonce = w3.eth.get_transaction_count(wallet_address)

            transaction = contract.constructor(*constructor_args).build_transaction({
                'from': wallet_address,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': network['chain_id'],
            })

            signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"TX Hash: {tx_hash.hex()} on {network['name']} ({network['chain_id']})")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Contract deployed at: {receipt.contractAddress} on {network['name']} ({network['chain_id']})")
            # Обновляем количество задеплоенных контрактов в JSON
            update_contract_count(wallet_address, network['name'])

            delay = get_random_delay()
            print(f"Waiting {delay:.2f} sec...")
            time.sleep(delay)

        else:
            print(f"Network {network['name']} has reached its contract limit for this wallet.")

            continue

    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
