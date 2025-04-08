import os
import json
from web3 import Web3
from decimal import Decimal
from dotenv import load_dotenv
import warnings

# Ignorer les avertissements spécifiques de Web3
warnings.filterwarnings('ignore', message='.*MismatchedABI.*')

# Charger les variables d'environnement
load_dotenv()

class DevineNombreInterface:
    def __init__(self, contract_address, abi_path):
        # Connexion au noeud Ethereum (Sepolia via Infura ou Ankr)
        rpc_url = os.getenv("ANKR_URL")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise Exception("❌ Échec de la connexion au noeud Ethereum.")
        print("✅ Connecté au noeud Ethereum.")

        # Charger l'ABI du contrat
        with open(abi_path, "r") as file:
            contract_abi = json.load(file)

        # Créer l'instance du contrat
        self.contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)

    def deviner_nombre(self, adresse_b, private_key_b, proposition):
        """Fonction pour que le joueur B fasse une proposition"""
        try:
            print(f"\nProposition : {proposition}")
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
                
                # Traiter les événements NombreDevine
                logs_devine = self.contract.events.NombreDevine().process_receipt(receipt)
                if logs_devine:
                    for log in logs_devine:
                        resultat = log['args']['resultat']
                        if resultat == "Plus petit":
                            print("📉 Votre nombre est TROP PETIT ! Essayez un nombre plus grand.")
                        elif resultat == "Plus grand":
                            print("📈 Votre nombre est TROP GRAND ! Essayez un nombre plus petit.")
                        elif resultat == "Correct !":
                            print("🎯 BRAVO ! Vous avez trouvé le nombre !")
                            return True

                # Traiter les événements JeuTermine
                jeu_termine = False
                logs_termine = self.contract.events.JeuTermine().process_receipt(receipt)
                if logs_termine:
                    for log in logs_termine:
                        print(f"\n🎮 {log['args']['message']}")
                        if "Tentatives epuises" in log['args']['message']:
                            print("❌ PERDU ! Vous n'avez plus de tentatives.")
                            jeu_termine = True
                            return True

                # Vérifier les tentatives restantes uniquement si le jeu n'est pas terminé
                if not jeu_termine:
                    tentatives = self.get_tentatives_restantes()
                    if tentatives == 0:
                        print("❌ Plus aucune tentative restante. Le jeu est terminé.")
                        return True
                    else:
                        print(f"Il vous reste {tentatives} tentative(s).")

                return False
            else:
                print("❌ La transaction a échoué.")
                return None

        except Exception as e:
            print(f"Erreur lors de l'envoi de la transaction : {e}")
            return None

    def get_etat(self):
        """Obtenir l'état du jeu"""
        try:
            etat = self.contract.functions.getEtat().call()
            print("État du jeu :", etat)
            return etat
        except Exception as e:
            print("Erreur lors de la récupération de l'état :", e)
            return None

    def get_tentatives_restantes(self):
        """Obtenir le nombre de tentatives restantes"""
        try:
            tentatives = self.contract.functions.getTentativesRestantes().call()
            print("Tentatives restantes :", tentatives)
            return tentatives
        except Exception as e:
            print("Erreur lors de la récupération des tentatives restantes :", e)
            return None

    def reinitialiser_jeu(self, nouveau_nombre_secret, nouveau_tentatives_max, private_key_a):
        """Réinitialiser le jeu avec un nouveau nombre secret et un nouveau nombre de tentatives"""
        try:
            print("Réinitialisation du jeu...")
            nonce = self.w3.eth.get_transaction_count(self.contract.functions.joueurA().call())
            gas_price = self.w3.eth.gas_price

            # Préparer la transaction
            tx = self.contract.functions.reinitialiserJeu(nouveau_nombre_secret, nouveau_tentatives_max).build_transaction({
                "from": self.contract.functions.joueurA().call(),
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": gas_price
            })

            # Signer et envoyer la transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key_a)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction de réinitialisation envoyée avec hash : {tx_hash.hex()}")

            # Attendre la confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt["status"] == 1:
                print("✅ Jeu réinitialisé avec succès.")
            else:
                print("❌ Échec de la réinitialisation du jeu.")
        except Exception as e:
            print(f"Erreur lors de la réinitialisation du jeu : {e}")


def main():
    # Charger les informations du contrat et des joueurs
    contract_address = "0xB7Fc7b14CCE0412ceF8E1118642831595D12cd82"
    abi_path = "Projet/abi_V1.json"
    private_key_a = "003a7c4f724e96a1dc87b1ce358db9e5875b4ae09650528d17df66e7134b5a2d"
    private_key_b = "616d22e8a70018af7832a42bdc01320b2ea726442a2e8665490d475f7f210f8d"
    account_a = Web3(Web3.HTTPProvider(os.getenv("INFURA_URL"))).eth.account.from_key(private_key_a)
    account_b = Web3(Web3.HTTPProvider(os.getenv("INFURA_URL"))).eth.account.from_key(private_key_b)

    # Vérifiez que les adresses sont différentes
    if account_a.address.lower() == account_b.address.lower():
        print(f"❌ Erreur : Les adresses du joueur A ({account_a.address}) et du joueur B ({account_b.address}) sont identiques.")
        return

    # Initialiser l'interface du contrat
    jeu = DevineNombreInterface(contract_address, abi_path)
    
    # Vérifier si le joueur B est déjà enregistré dans le contrat
    joueur_b = jeu.contract.functions.joueurB().call()
    if joueur_b == "0x0000000000000000000000000000000000000000":
        print("⚠️ Le joueur B n'est pas encore enregistré. Enregistrement en cours...")
        try:
            nonce = jeu.w3.eth.get_transaction_count(account_b.address)
            tx = jeu.contract.functions.deviner(0).build_transaction({
                "from": account_b.address,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": jeu.w3.eth.gas_price
            })
            signed_tx = jeu.w3.eth.account.sign_transaction(tx, private_key_b)
            tx_hash = jeu.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction d'enregistrement envoyée avec hash : {tx_hash.hex()}")
            receipt = jeu.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt["status"] == 1:
                print("✅ Joueur B enregistré avec succès.")
            else:
                print("❌ Échec de l'enregistrement du joueur B.")
                return
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du joueur B : {e}")
            return
    elif joueur_b.lower() != account_b.address.lower():
        print(f"❌ Erreur : L'adresse {account_b.address} n'est pas enregistrée comme joueur B.")
        return

    # Vérifier l'état du jeu
    etat = jeu.get_etat()
    if etat == "Termine":
        print("Le jeu est terminé. Réinitialisation en cours...")
        jeu.reinitialiser_jeu(nouveau_nombre_secret=42, nouveau_tentatives_max=5, private_key_a=private_key_a)

    # Boucle principale pour deviner le nombre
    try:
        jeu.get_etat()
        jeu.get_tentatives_restantes()

        while True:
            proposition = input("Entrez votre proposition (ou 'exit' pour quitter) : ")
            if proposition.lower() == "exit":
                print("Fin du jeu.")
                break
            try:
                proposition = int(proposition)
                game_over = jeu.deviner_nombre(account_b.address, private_key_b, proposition)
                jeu.get_etat()
                jeu.get_tentatives_restantes()
                if game_over:
                    print("Le jeu est terminé.")
                    break
            except ValueError:
                print("Veuillez entrer un nombre valide.")
            except Exception as e:
                print(f"Erreur lors de la tentative : {e}")
    except Exception as e:
        print(f"Erreur initiale : {e}")


if __name__ == "__main__":
    main()
