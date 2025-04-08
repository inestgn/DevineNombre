import hashlib
import requests

def sha256(data):
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

# Fonction pour construire un arbre de Merkle et retourner la racine
def construct_merkle_tree(transactions):
    if not transactions:
        raise ValueError("Aucune transaction fournie")

    # Initialisation
    current_level = [sha256(tx) for tx in transactions]

    # Construction de l'arbre jusqu'à la racine
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            next_level.append(sha256(left + right))
        current_level = next_level

    # Racine est le seul élément restant
    return current_level[0]

# Fonction pour générer une preuve de Merkle pour une transac 
def generate_merkle_proof(transactions, target_tx):
    if target_tx not in transactions:
        raise ValueError("La transaction n'est pas dans la liste")

    # Initialisation
    current_level = [sha256(tx) for tx in transactions]
    proof = []
    index = transactions.index(target_tx)

    # Construction de l'arbre
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            combined = sha256(left + right)
            next_level.append(combined)

            # Enregistrement des données preuve
            if i == index or i + 1 == index:
                neigh = right if i == index else left
                proof.append((neigh, 'right' if i == index else 'left'))

        index //= 2
        current_level = next_level

    return proof

def verify_merkle_proof(root, target_tx, proof):
    current_hash = sha256(target_tx)

    for neigh, direction in proof:
        if direction == 'left':
            current_hash = sha256(neigh + current_hash)
        else:
            current_hash = sha256(current_hash + neigh)

    return current_hash == root

def get_block_data(block_hash):
    url = f'https://blockstream.info/api/block/{block_hash}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur: {response.status_code}")
        return None

def get_block_transactions(block_hash):
    url = f'https://blockstream.info/api/block/{block_hash}/txids'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur lors de la récupération des transactions: {response.status_code}")
        return None

def process_block(block_hash, target_tx):
    block_data = get_block_data(block_hash)
    if not block_data:
        raise ValueError("Impossible de récupérer les données du bloc")

    transactions = get_block_transactions(block_hash)
    if not transactions:
        raise ValueError("Impossible de récupérer les transactions du bloc")

    # Étape 1 : Calcul de la racine de Merkle
    root = construct_merkle_tree(transactions)

    # Étape 2 : Génération de la preuve de Merkle pour la transaction cible
    proof = generate_merkle_proof(transactions, target_tx)

    # Étape 3 : Vérification de la preuve
    is_valid = verify_merkle_proof(root, target_tx, proof)

    return root, proof, is_valid

# Exemple d'utilisation
if __name__ == "__main__":
    # Remplacer par un vrai hash de bloc et une transaction réelle
    block_hash = "00000000000000000001f89205233a70132556d6f52c3680f2e242792e838f2e"
    target_tx = "ad10ca1b04dae3aa516ebdd21a9aba046f54b7f537a61b276bd137fa090f859f"

    # Traitement du bloc
    try:
        root, proof, is_valid = process_block(block_hash, target_tx)
        print("Racine de Merkle:", root)
        print("Preuve de Merkle:", proof)
        print("La preuve est-elle valide ?", is_valid)
    except ValueError as e:
        print("Erreur:", e)
