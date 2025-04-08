import os
import json
import warnings
from web3 import Web3
from decimal import Decimal
from dotenv import load_dotenv

# Ignorer les avertissements spécifiques de Web3
warnings.filterwarnings('ignore', message='.*MismatchedABI.*')

# Charger les variables d'environnement
load_dotenv()

class DevineNombreAvecMiseInterface:
    def __init__(self, contract_address, abi_path):
        rpc_url = os.getenv("ANKR_URL")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise Exception("❌ Échec de la connexion au noeud Ethereum.")
        print("✅ Connecté au noeud Ethereum.")

        with open(abi_path, "r") as file:
            contract_abi = json.load(file)

        self.contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)

    def get_mise_a(self):
        """Obtenir la mise du joueur A"""
        try:
            mise = self.contract.functions.miseA().call()
            return self.w3.from_wei(mise, 'ether')
        except Exception as e:
            print(f"Erreur lors de la récupération de la mise A : {e}")
            return 0

    def get_mise_b(self):
        """Obtenir la mise du joueur B"""
        try:
            mise = self.contract.functions.miseB().call()
            return self.w3.from_wei(mise, 'ether')
        except Exception as e:
            print(f"Erreur lors de la récupération de la mise B : {e}")
            return 0

    def participer(self, adresse_b, private_key_b, mise):
        try:
            print(f"Participation du joueur B avec {mise} ETH...")
            nonce = self.w3.eth.get_transaction_count(adresse_b)
            gas_price = self.w3.eth.gas_price

            tx = self.contract.functions.participer().build_transaction({
                "from": adresse_b,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": gas_price,
                "value": self.w3.to_wei(mise, "ether")
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key_b)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction envoyée avec hash : {tx_hash.hex()}")

            print("Attente de la confirmation de la transaction...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt["status"] == 1:
                print(f"✅ Participation réussie. Transaction incluse dans le bloc {receipt['blockNumber']}.")
                print(f"📜 Logs de la transaction : {receipt['logs']}")
                return True
            else:
                print("❌ La transaction a échoué.")
                print(f"📜 Receipt complet : {receipt}")
                print(f"📜 Gas utilisé : {receipt['gasUsed']}")
                print(f"📜 Logs Bloom : {receipt['logsBloom']}")
                return False
        except Exception as e:
            print(f"Erreur lors de la participation : {e}")
            return False

    def reinitialiser_jeu(self, nouveau_nombre_secret, nouveau_tentatives_max, mise_a, private_key_a):
        try:
            print("Réinitialisation du jeu...")
            nonce = self.w3.eth.get_transaction_count(self.contract.functions.joueurA().call())
            gas_price = self.w3.eth.gas_price

            tx = self.contract.functions.reinitialiserJeu(nouveau_nombre_secret, nouveau_tentatives_max).build_transaction({
                "from": self.contract.functions.joueurA().call(),
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": gas_price,
                "value": self.w3.to_wei(mise_a, "ether")
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key_a)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print(f"Transaction de réinitialisation envoyée avec hash : {tx_hash.hex()}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt["status"] == 1:
                print("✅ Jeu réinitialisé avec succès.")
            else:
                print("❌ Échec de la réinitialisation du jeu.")
        except Exception as e:
            print(f"Erreur lors de la réinitialisation du jeu : {e}")

    def deviner_nombre(self, adresse_b, private_key_b, proposition):
        try:
            print(f"Envoi de la proposition : {proposition}")
            nonce = self.w3.eth.get_transaction_count(adresse_b)
            gas_price = self.w3.eth.gas_price

            tx = self.contract.functions.deviner(proposition).build_transaction({
                "from": adresse_b,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": gas_price
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key_b)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction envoyée avec hash : {tx_hash.hex()}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt["status"] == 1:
                print(f"✅ Transaction incluse dans le bloc : {receipt['blockNumber']}")
                try:
                    logs_devine = self.contract.events.NombreDevine().process_receipt(receipt)
                    if logs_devine:
                        for log in logs_devine:
                            print(f"📣 NombreDevine | Proposition : {log['args']['proposition']} - Résultat : {log['args']['resultat']}")

                    logs_termine = self.contract.events.JeuTermine().process_receipt(receipt)
                    if logs_termine:
                        for log in logs_termine:
                            print(f"🎉 JeuTermine | Message : {log['args']['message']}")
                        return True
                except Exception:
                    pass
                return False
            else:
                print("❌ La transaction a échoué.")
                return None
        except Exception as e:
            print(f"Erreur lors de l'envoi de la transaction : {e}")
            return None

def main():
    contract_address = "0x82043c11F6Af3142a723Edc5867B8c31486eb4BD"
    abi_path = "Projet/abi_V2.json"
    private_key_a = os.getenv("PRIVATE_KEY_A")
    private_key_b = os.getenv("PRIVATE_KEY_B")
    account_a = Web3(Web3.HTTPProvider("https://rpc.ankr.com/eth_sepolia/a2fc2d9e983406edd9fe27ba7ebe770465a1b489c2b245f13d0c11bf1db16d2f")).eth.account.from_key(private_key_a)
    account_b = Web3(Web3.HTTPProvider("https://rpc.ankr.com/eth_sepolia/a2fc2d9e983406edd9fe27ba7ebe770465a1b489c2b245f13d0c11bf1db16d2f")).eth.account.from_key(private_key_b)

    # Vérification explicite de la connexion au nœud Ankr
    try:
        print("Vérification de la connexion au nœud Ankr...")
        w3 = Web3(Web3.HTTPProvider(os.getenv("ANKR_URL")))
        if not w3.is_connected():
            print("❌ Échec de la connexion au nœud Ankr. Vérifiez l'URL ou votre connexion Internet.")
            return
        print("✅ Connexion réussie au nœud Ankr.")
        print(f"Version du client Ethereum : {w3.client_version}")
        print(f"Numéro du dernier bloc : {w3.eth.block_number}")
    except Exception as e:
        print(f"❌ Erreur lors de la connexion au nœud Ankr : {e}")
        return

    jeu = DevineNombreAvecMiseInterface(contract_address, abi_path)

    print("\n--- Infos Debug ---")
    print(f"Adresse du joueur A : {account_a.address}")
    print(f"Adresse du joueur B : {account_b.address}")
    print(f"Adresse du contrat : {contract_address}")

    # Vérifier l'état du jeu
    etat = jeu.contract.functions.getEtat().call()
    print(f"État du jeu : {etat}")
    if etat == "En attente":
        print("⚠️ Le jeu est en attente. Le joueur A doit redémarrer le jeu.")
        return
    elif etat != "En cours":
        print("❌ Erreur : Le jeu n'est pas en cours.")
        return

    # Vérifier le propriétaire du contrat (joueur A)
    joueur_a_contract = jeu.contract.functions.joueurA().call()
    print(f"Adresse du joueur A dans le contrat : {joueur_a_contract}")
    
    if joueur_a_contract.lower() != account_a.address.lower():
        print("❌ Erreur : L'adresse du joueur A ne correspond pas au propriétaire du contrat.")
        return

    # Vérifier l'état du jeu
    etat = jeu.contract.functions.getEtat().call()
    print(f"État du jeu : {etat}")
    if etat != "En cours":
        print("❌ Erreur : Le jeu n'est pas en cours.")
        return

    # Obtenir et vérifier la mise
    try:
        mise_a = jeu.contract.functions.miseA().call()
        mise_minimale_eth = Web3.from_wei(mise_a, 'ether')
        print(f"Mise du joueur A : {mise_minimale_eth} ETH")
        
        # Définir une mise minimale absolue de 0.001 ETH pour couvrir les frais de gas
        MISE_MINIMALE_ABSOLUE = 0.001  # 0.001 ETH minimum
        
        if float(mise_minimale_eth) < MISE_MINIMALE_ABSOLUE:
            print(f"❌ La mise du joueur A ({mise_minimale_eth} ETH) est trop faible.")
            print(f"La mise minimale requise est de {MISE_MINIMALE_ABSOLUE} ETH pour couvrir les frais de gas.")
            print("Veuillez demander au joueur A de recréer une partie avec une mise plus élevée.")
            return
        
        # Demander la mise au joueur B
        while True:
            try:
                mise_b = float(input(f"Entrez votre mise en ETH (minimum {mise_minimale_eth} ETH) : "))
                if mise_b < MISE_MINIMALE_ABSOLUE:
                    print(f"❌ La mise doit être au moins de {MISE_MINIMALE_ABSOLUE} ETH pour couvrir les frais de gas")
                    continue
                if mise_b < float(mise_minimale_eth):
                    print(f"❌ La mise doit être au moins égale à celle du joueur A ({mise_minimale_eth} ETH)")
                    continue
                break
            except ValueError:
                print("❌ Veuillez entrer un nombre valide")

        # Participation et jeu
        print("\nParticipation du joueur B...")
        if not jeu.participer(account_b.address, private_key_b, mise=mise_b):
            print("❌ Échec de la participation. Arrêt du programme.")
            return

        print("\nVérification de l'état après participation...")
        joueur_b_contract = jeu.contract.functions.joueurB().call()
        mise_b_contract = jeu.contract.functions.miseB().call()
        print(f"Adresse du joueur B dans le contrat : {joueur_b_contract}")
        print(f"Mise du joueur B dans le contrat : {Web3.from_wei(mise_b_contract, 'ether')} ETH")

        if joueur_b_contract.lower() != account_b.address.lower():
            print("❌ Erreur : La participation du joueur B n'a pas été enregistrée correctement.")
            return

        print("\nDébut du jeu - Tentez de deviner le nombre!")
        while True:
            # Afficher l'état actuel
            etat = jeu.contract.functions.getEtat().call()
            tentatives = jeu.contract.functions.getTentativesRestantes().call()
            print(f"\nÉtat du jeu : {etat}")
            print(f"Tentatives restantes : {tentatives}")

            proposition = input("\nEntrez votre proposition (ou 'exit' pour quitter) : ")
            if proposition.lower() == "exit":
                print("Fin du jeu.")
                break
            try:
                proposition = int(proposition)
                result = jeu.deviner_nombre(account_b.address, private_key_b, proposition)
                if result:
                    print("Le jeu est terminé.")
                    break
            except ValueError:
                print("❌ Veuillez entrer un nombre valide.")
            except Exception as e:
                print(f"❌ Erreur lors de la tentative : {e}")

    except Exception as e:
        print(f"❌ Erreur initiale : {e}")

if __name__ == "__main__":
    main()
