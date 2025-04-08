import solcx
from web3 import Web3
from eth_account import Account
import time  # Ajout de l'import pour gérer les délais

# === Configuration ===
solcx.set_solc_version("0.8.29")

# === Clés et URL ===
url_ankr = "https://rpc.ankr.com/eth_sepolia/a2fc2d9e983406edd9fe27ba7ebe770465a1b489c2b245f13d0c11bf1db16d2f"
private_key_B = "616d22e8a70018af7832a42bdc01320b2ea726442a2e8665490d475f7f210f8d"
private_key_A = "003a7c4f724e96a1dc87b1ce358db9e5875b4ae09650528d17df66e7134b5a2d"

# === Initialisation Web3 ===
web3 = Web3(Web3.HTTPProvider(url_ankr))
assert web3.is_connected(), "Connexion échouée au noeud Ankr"

# Configuration EIP-155
SEPOLIA_CHAIN_ID = 11155111
account_A = Account.from_key(private_key_A)
account_B = Account.from_key(private_key_B)

# === Chargement du contrat ===
with open("/home/ines/Documents/M2/Blockchain/Projet/V1.sol", "r") as f:
    contract_source_code = f.read()

compiled_sol = solcx.compile_source(
    contract_source_code,
    output_values=["abi", "bin"],
    optimize=True,
    optimize_runs=200
)
contract_id, contract_interface = compiled_sol.popitem()
abi = contract_interface["abi"]
bytecode = contract_interface["bin"]

def deploy_contract(nombre_secret, tentatives_max):
    # 1. Vérification des fonds
    balance = web3.eth.get_balance(account_A.address)
    print(f"Solde compte A: {web3.from_wei(balance, 'ether')} ETH")
    
    if balance < web3.to_wei(0.005, 'ether'):  # Réduction du seuil minimum
        raise ValueError("Fonds insuffisants pour déployer le contrat")

    # 2. Construction transaction
    contract = web3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = web3.eth.get_transaction_count(account_A.address, 'pending')
    
    tx = contract.constructor(nombre_secret, tentatives_max).build_transaction({
        'chainId': SEPOLIA_CHAIN_ID,
        'from': account_A.address,
        'nonce': nonce,
        'gas': 1_000_000,  # Réduction de la limite de gaz
        'gasPrice': web3.to_wei('5', 'gwei')  # Réduction du gasPrice
    })

    # 3. Signature et envoi
    signed_tx = account_A.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Transaction envoyée: {tx_hash.hex()}")
    print(f"Suivi: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
    
    # Vérification locale de la transaction
    try:
        tx = None
        retries = 10  # Augmentation du nombre de tentatives
        for attempt in range(retries):
            try:
                tx = web3.eth.get_transaction(tx_hash)
                print(f"Transaction récupérée localement : {tx}")
                break
            except Exception as e:
                print(f"Tentative {attempt + 1}/{retries} : Transaction introuvable. Réessai dans 5 secondes...")
                time.sleep(5)  # Augmentation du délai entre les tentatives
        if tx is None:
            # Ajout d'un diagnostic supplémentaire
            print("Diagnostic : Vérification du numéro de bloc actuel...")
            print(f"Numéro de bloc actuel : {web3.eth.block_number}")
            raise Exception("La transaction n'a pas été correctement envoyée après plusieurs tentatives.")
    except Exception as e:
        print(f"Erreur : Impossible de récupérer la transaction localement. {e}")
        raise Exception("La transaction n'a pas été correctement envoyée.")

    # 4. Attente confirmation
    try:
        print("Attente de la confirmation de la transaction...")
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        print(f"Contrat déployé à: {tx_receipt.contractAddress}")
        print(f"Code du contrat : {web3.eth.get_code(tx_receipt.contractAddress).hex()}")
        if web3.eth.get_code(tx_receipt.contractAddress) == b'':
            raise Exception("Le contrat n'a pas été correctement déployé.")
        return web3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
    except Exception as e:
        print(f"Erreur lors de la confirmation de la transaction : {e}")
        raise

def deviner_nombre(contract, joueur, private_key, proposition):
    account = Account.from_key(private_key)
    nonce = web3.eth.get_transaction_count(account.address, 'pending')
    
    tx = contract.functions.deviner(proposition).build_transaction({
        'chainId': SEPOLIA_CHAIN_ID,
        'from': account.address,
        'nonce': nonce,
        'gas': 100_000,  # Réduction de la limite de gaz
        'gasPrice': web3.to_wei('5', 'gwei')  # Réduction du gasPrice
    })
    
    signed_tx = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Vérification des événements
    logs = contract.events.NombreDevine().process_receipt(receipt)
    if logs:
        print(f"Résultat: {logs[0]['args']['resultat']}")
    
    print(f"Transaction: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")

if __name__ == "__main__":
    print("Déploiement du contrat...")
    try:
        contrat = deploy_contract(nombre_secret=42, tentatives_max=5)  # Réduction des tentatives max
        print("Contrat déployé avec succès. Adresse :", contrat.address)
    except Exception as e:
        print(f"Erreur critique lors du déploiement : {e}")
        exit()

    # Boucle de jeu
    while True:
        try:
            proposition = int(input("\nProposition (ou -1 pour quitter): "))
            
            if proposition == -1:
                break
                
            print("\nJoueur B tente de deviner...")
            deviner_nombre(contrat, account_B, private_key_B, proposition)
            
            if contrat.functions.getEtat().call() == "Termine":
                print("\nJeu terminé!")
                balance = web3.eth.get_balance(account_B.address)
                print(f"Solde du Joueur B: {web3.from_wei(balance, 'ether')} ETH")
                break
                
        except ValueError:
            print("Erreur: Entrez un nombre valide")
        except Exception as e:
            print(f"Erreur: {str(e)}")
            break
