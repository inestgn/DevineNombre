import requests
import json

def get_block_data(block_hash):
    url = f'https://blockstream.info/api/block/{block_hash}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur récupération bloc: {response.status_code}")
        return None

def get_block_transactions(block_hash):
    url = f'https://blockstream.info/api/block/{block_hash}/txids'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur récupération transaction: {response.status_code}")
        return None

def get_transaction_data(txid):
    url = f'https://blockstream.info/api/tx/{txid}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur récupération data: {response.status_code}")
        return None

def find_largest_transaction(block_hash):
    txids = get_block_transactions(block_hash)
    if not txids:
        return None

    largest_tx = None
    largest_amount = 0

    for txid in txids:
        tx_data = get_transaction_data(txid)
        if not tx_data:
            continue
        total_output = sum(output['value'] for output in tx_data['vout'])
        if total_output > largest_amount:
            largest_amount = total_output
            largest_tx = tx_data

    return largest_tx

if __name__ == "__main__":
    hash = '00000000000000000002612d14643904fab690a42f6b3b78438bde6911cef3bc'
    largest_tx = find_largest_transaction(hash)
    if largest_tx:
        print("Transaction avec le plus gros montant échangé :")
        print(json.dumps(largest_tx, indent=4))
    else:
        print("Aucune transaction trouvée ou erreur lors de la récupération des données.")

# Exemples de transactions : 
# 000000000000000000025a431d550872d5643cf086ce3ac46df30bd9863261f5 (1  transac)
# 00000000000000000000a653b9d06e81f3060a93eded94231618d7d6b35a04ce (230 transac)
# 00000000000000000002612d14643904fab690a42f6b3b78438bde6911cef3bc (73 transac)
# 000000000000000000005bac94414e1b9ab0975dc81fb6c16dc8bbfa3a83d298 ( 2 transac)