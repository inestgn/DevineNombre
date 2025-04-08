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

            # Augmenter la limite de gas
            gas_estimate = self.contract.functions.participer().estimate_gas({
                "from": adresse_b,
                "value": self.w3.to_wei(mise, "ether")
            })
            print(f"Gas estimé : {gas_estimate}")
            
            tx = self.contract.functions.participer().build_transaction({
                "from": adresse_b,
                "nonce": nonce,
                "gas": gas_estimate * 2,  # Double du gas estimé pour plus de sécurité
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
                # Vérification supplémentaire
                joueur_b = self.contract.functions.joueurB().call()
                print(f"Debug - Nouveau joueur B enregistré : {joueur_b}")
                mise_b = self.contract.functions.miseB().call()
                print(f"Debug - Nouvelle mise B enregistrée : {self.w3.from_wei(mise_b, 'ether')} ETH")
                return True
            else:
                print("❌ La transaction a échoué.")
                print(f"Debug - Receipt complet : {receipt}")
                # Essayer de récupérer la raison de l'échec
                try:
                    reason = self.w3.eth.call({
                        "from": adresse_b,
                        "to": self.contract.address,
                        "data": tx["data"],
                        "value": tx["value"],
                        "gas": tx["gas"],
                        "gasPrice": tx["gasPrice"],
                        "nonce": tx["nonce"]
                    })
                    print(f"Debug - Raison de l'échec : {reason}")
                except Exception as call_error:
                    print(f"Debug - Erreur lors de l'appel de test : {call_error}")
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
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
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

            # Estimer le gas nécessaire
            gas_estimate = self.contract.functions.deviner(proposition).estimate_gas({
                "from": adresse_b
            })
            # Multiplier par 3 pour assurer assez de gas pour le transfert d'ETH
            gas = gas_estimate * 3

            tx = self.contract.functions.deviner(proposition).build_transaction({
                "from": adresse_b,
                "nonce": nonce,
                "gas": max(gas, 800000),  # Au moins 800000 de gas pour le transfert
                "gasPrice": gas_price
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key_b)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction envoyée avec hash : {tx_hash.hex()}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt["status"] == 1:
                print(f"✅ Transaction incluse dans le bloc : {receipt['blockNumber']}")
                try:
                    logs_termine = self.contract.events.JeuTermine().process_receipt(receipt)
                    if logs_termine:
                        for log in logs_termine:
                            message = log['args']['message']
                            print(f"\n🎮 {message}")
                            return True  # Si on a un événement JeuTermine, c'est que le jeu est fini

                    logs_devine = self.contract.events.NombreDevine().process_receipt(receipt)
                    if logs_devine:
                        for log in logs_devine:
                            resultat = log['args']['resultat']
                            print(f"📣 NombreDevine | Proposition : {log['args']['proposition']} - Résultat : {resultat}")
                            
                            # Ne pas retourner True tout de suite si c'est correct, le transfert doit se faire
                            if resultat == "Correct !":
                                print("\n🎉 FÉLICITATIONS ! Vous avez gagné ! Les mises vous sont transférées.")

                    # Vérifier les tentatives après tout
                    tentatives = self.contract.functions.getTentativesRestantes().call()
                    print(f"\n🎲 Il vous reste {tentatives} tentative(s)")

                    return False
                except Exception as e:
                    print(f"Erreur lors du traitement des événements : {e}")
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
    account_a = Web3(Web3.HTTPProvider(os.getenv("ANKR_URL"))).eth.account.from_key(private_key_a)
    account_b = Web3(Web3.HTTPProvider(os.getenv("ANKR_URL"))).eth.account.from_key(private_key_b)
    
    try:
        # Vérification de la connexion
        print("Vérification de la connexion au nœud Ankr...")
        w3 = Web3(Web3.HTTPProvider(os.getenv("ANKR_URL")))
        if not w3.is_connected():
            print("❌ Échec de la connexion au nœud Ankr.")
            return
        print("✅ Connexion réussie au nœud Ankr.")
        
        jeu = DevineNombreAvecMiseInterface(contract_address, abi_path)

        # Vérifier si un joueur B existe déjà
        try:
            joueur_b_existant = jeu.contract.functions.joueurB().call()
            if joueur_b_existant != "0x0000000000000000000000000000000000000000":
                # Si le joueur B existe et qu'il s'agit de notre adresse, on peut continuer
                if joueur_b_existant.lower() == account_b.address.lower():
                    print("✅ Vous êtes déjà enregistré comme joueur B. Début du jeu...")
                    # Passer directement à la phase de jeu
                    print("\nDébut du jeu - Tentez de deviner le nombre!")
                    while True:
                        try:
                            proposition = input("\nEntrez votre proposition (ou 'exit' pour quitter) : ")
                            if proposition.lower() == "exit":
                                break
                            proposition = int(proposition)
                            result = jeu.deviner_nombre(account_b.address, private_key_b, proposition)
                            if result:
                                print("Le jeu est terminé.")
                                break
                        except ValueError:
                            print("❌ Veuillez entrer un nombre valide.")
                        except Exception as e:
                            print(f"❌ Erreur lors de la tentative : {e}")
                            break
                    return
                else:
                    print("❌ Un autre joueur B est déjà enregistré pour cette partie.")
                    return
        except Exception as e:
            print(f"Erreur lors de la vérification du joueur B : {e}")
            return

        # Si on arrive ici, c'est qu'il n'y a pas encore de joueur B
        # Continuer avec le code existant pour la participation...
        print("\nRéinitialisation du jeu...")
        try:
            tx = jeu.contract.functions.reinitialiserJeu(
                44,  # nombre secret
                5   # tentatives max
            ).build_transaction({
                "from": account_a.address,
                "nonce": w3.eth.get_transaction_count(account_a.address),
                "gas": 300000,
                "gasPrice": w3.eth.gas_price,
                "value": w3.to_wei(0.001, "ether")
            })
            signed_tx = w3.eth.account.sign_transaction(tx, private_key_a)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            w3.eth.wait_for_transaction_receipt(tx_hash)
            print("✅ Jeu réinitialisé avec succès")

            # Continuer directement avec le reste du programme
            print("\n--- Infos Debug ---")
            print(f"Adresse du joueur A : {account_a.address}")
            print(f"Adresse du joueur B : {account_b.address}")
            print(f"Adresse du contrat : {contract_address}")

            # Vérifications de l'état du jeu
            etat = jeu.contract.functions.getEtat().call()
            print(f"État du jeu : {etat}")
            if etat != "En cours":
                print("❌ Erreur : Le jeu n'est pas en cours.")
                return

            # Vérifications du joueur A et de la mise
            mise_a = jeu.contract.functions.miseA().call()
            mise_minimale_eth = Web3.from_wei(mise_a, 'ether')
            print(f"Mise du joueur A : {mise_minimale_eth} ETH")
            
            MISE_MINIMALE_ABSOLUE = 0.001
            if float(mise_minimale_eth) < MISE_MINIMALE_ABSOLUE:
                print(f"❌ La mise du joueur A ({mise_minimale_eth} ETH) est trop faible.")
                print(f"La mise minimale requise est de {MISE_MINIMALE_ABSOLUE} ETH")
                return

            # Boucle de saisie de la mise du joueur B
            while True:
                try:
                    mise_b = float(input(f"Entrez votre mise en ETH (minimum {mise_minimale_eth} ETH) : "))
                    if mise_b >= float(mise_minimale_eth) and mise_b >= MISE_MINIMALE_ABSOLUE:
                        break
                    print(f"❌ La mise doit être au moins de {max(mise_minimale_eth, MISE_MINIMALE_ABSOLUE)} ETH")
                except ValueError:
                    print("❌ Veuillez entrer un nombre valide")

            # Participation et jeu
            if not jeu.participer(account_b.address, private_key_b, mise=mise_b):
                print("❌ Échec de la participation. Arrêt du programme.")
                return

            # Boucle de jeu
            print("\nDébut du jeu - Tentez de deviner le nombre!")
            while True:
                try:
                    proposition = input("\nEntrez votre proposition (ou 'exit' pour quitter) : ")
                    if proposition.lower() == "exit":
                        break

                    proposition = int(proposition)
                    result = jeu.deviner_nombre(account_b.address, private_key_b, proposition)
                    if result:
                        print("Le jeu est terminé.")
                        break

                except ValueError:
                    print("❌ Veuillez entrer un nombre valide.")
                except Exception as e:
                    print(f"❌ Erreur lors de la tentative : {e}")
                    break

        except Exception as e:
            print(f"⚠️ Erreur lors de la réinitialisation : {e}")
            return

    except Exception as e:
        print(f"❌ Erreur principale : {e}")

if __name__ == "__main__":
    main()