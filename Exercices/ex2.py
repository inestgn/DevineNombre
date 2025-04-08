import requests
from collections import defaultdict

def get_block_hash(height):
    url = f'https://blockstream.info/api/block-height/{height}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Erreur lors de la récupération du hash à hauteur {height}: {response.status_code}")
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

def find_most_frequent_address(h1, h2):
    address_count = defaultdict(int)

    for height in range(h1, h2 + 1):
        block_hash = get_block_hash(height)
        if not block_hash:
            continue
        txids = get_block_transactions(block_hash)
        if not txids:
            continue
        for txid in txids:
            tx_data = get_transaction_data(txid)
            if not tx_data:
                continue
            for output in tx_data['vout']:
                address = output.get('scriptpubkey_address')
                if address:
                    address_count[address] += 1

    if not address_count:
        return None, 0

    most_frequent_address = max(address_count, key=address_count.get)
    return most_frequent_address, address_count[most_frequent_address]

if __name__ == "__main__":
    h1 = 100000 
    h2 = 100020 
    address, count = find_most_frequent_address(h1, h2)
    if address:
        print(f"L'adresse bitcoin la plus fréquente est : {address}")
        print(f"Elle apparaît {count} fois.")
    else:
        print("Aucune adresse trouvée ou erreur lors de la récupération des données.")