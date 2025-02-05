import aiohttp
import asyncio
from web3 import Web3
from eth_account import Account
from time import sleep

def bridge_eth(private_key, eth_to_bridge, from_chain, to_chain, rpc_nodes, max_attempts=3):
    web3 = Web3(Web3.HTTPProvider(rpc_nodes[from_chain]))
    account = Account.from_key(private_key)

    async def get_quote():
        headers = {
            'accept': 'application/json, text/plain, */*',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
        }
        wei_amount_str = str(int(eth_to_bridge))  # Преобразуем в int, затем в строку

        json_data = {
            'user': account.address.lower(),
            'originChainId': from_chain,
            'destinationChainId': to_chain,
            'originCurrency': '0x0000000000000000000000000000000000000000',
            'destinationCurrency': '0x0000000000000000000000000000000000000000',
            'recipient': account.address,
            'tradeType': 'EXACT_INPUT',
            'amount': wei_amount_str,
            'referrer': 'relay.link/swap',
            'slippageTolerance': '',
            'useExternalLiquidity': False,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.relay.link/quote', headers=headers, json=json_data) as response:
                print(f"Response Status: {response.status}")
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error Response: {await response.text()}")
                    return None

    async def send_transaction(quote_data):
        if not quote_data:
            print("❌ Ошибка: нет данных котировки")
            return False
        
        try:
            tx_data = quote_data['steps'][0]['items'][0]['data']
        except (KeyError, IndexError) as e:
            print(f"Ошибка в структуре данных котировки: {e}")
            return False
        
        transaction = {
            'from': account.address,
            'to': Web3.to_checksum_address(tx_data['to']),
            'value': int(tx_data['value']),
            'data': tx_data['data'],
            'chainId': int(tx_data['chainId']),
            'maxFeePerGas': int(tx_data['maxFeePerGas']),
            'maxPriorityFeePerGas': int(tx_data['maxPriorityFeePerGas']),
            'nonce': web3.eth.get_transaction_count(account.address),
            'type': 2
        }

        try:
            gas_estimate = web3.eth.estimate_gas(transaction)
        except Exception as e:
            print(f"Ошибка при оценке газа: {e}")
            return False
        
        transaction['gas'] = int(gas_estimate * 1.1)

        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"🚀 Транзакция отправлена: {tx_hash.hex()}")

        try:
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt['status'] == 1:
                print(f"✅ Транзакция подтверждена: {tx_hash.hex()}")
                return True
            else:
                print(f"❌ Транзакция не удалась: {tx_hash.hex()}")
                return False
        except Exception as e:
            print(f"Ошибка при ожидании подтверждения транзакции: {e}")
            return False

    async def main():
        attempt = 0
        while attempt < max_attempts:
            print(f"Попытка {attempt + 1}/{max_attempts}...")
            quote_data = await get_quote()
            if await send_transaction(quote_data):
                return True  # Если транзакция успешно отправлена, завершаем
            attempt += 1
            print("Повторная попытка...")
            sleep(5)  # Ожидаем 5 секунд перед повторной попыткой

        print("Максимальное количество попыток исчерпано.")
        return False

    return asyncio.run(main())
