import os
import json
import warnings  # Import pour gérer les avertissements
from web3 import Web3
from dotenv import load_dotenv

# Ignorer les avertissements spécifiques de Web3
warnings.filterwarnings('ignore', message='.*MismatchedABI.*')

# Charger les variables d'environnement
load_dotenv()

class DevineNombreGeneriqueInterface:
    def __init__(self, contract_address, abi_path):
        # Connexion au noeud Ethereum
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

    def creer_jeu(self, nombre_secret, tentatives_max, mise_a, private_key_a):
        """Créer un nouveau jeu"""
        try:
            print("Création d'un nouveau jeu...")
            # Récupérer l'adresse du joueur A à partir de la clé privée
            adresse_a = self.w3.eth.account.from_key(private_key_a).address
            nonce = self.w3.eth.get_transaction_count(adresse_a)
            gas_price = self.w3.eth.gas_price

            tx = self.contract.functions.creerJeu(nombre_secret, tentatives_max).build_transaction({
                "from": adresse_a,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": gas_price,
                "value": self.w3.to_wei(mise_a, "ether")
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key_a)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction de création envoyée avec hash : {tx_hash.hex()}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt["status"] == 1:
                print("✅ Jeu créé avec succès.")
            else:
                print("❌ Échec de la création du jeu.")
        except Exception as e:
            print(f"Erreur lors de la création du jeu : {e}")

    def participer(self, id_jeu, mise_b, adresse_b, private_key_b):
        """Participer à un jeu en tant que joueur B"""
        try:
            print(f"Participation au jeu {id_jeu} avec une mise de {mise_b} ETH...")
            nonce = self.w3.eth.get_transaction_count(adresse_b)
            gas_price = self.w3.eth.gas_price

            tx = self.contract.functions.participer(id_jeu).build_transaction({
                "from": adresse_b,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": gas_price,
                "value": self.w3.to_wei(mise_b, "ether")
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key_b)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction de participation envoyée avec hash : {tx_hash.hex()}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt["status"] == 1:
                print("✅ Participation réussie.")
            else:
                print("❌ Échec de la participation.")
                print(f"📜 Receipt complet : {receipt}")
                print(f"📜 Gas utilisé : {receipt['gasUsed']}")
                print(f"📜 Logs Bloom : {receipt['logsBloom']}")
        except Exception as e:
            print(f"Erreur lors de la participation : {e}")

    def deviner_nombre(self, id_jeu, proposition, adresse_b, private_key_b):
        """Deviner un nombre dans un jeu"""
        try:
            print(f"Proposition pour le jeu {id_jeu} : {proposition}")
            nonce = self.w3.eth.get_transaction_count(adresse_b)
            gas_price = self.w3.eth.gas_price

            tx = self.contract.functions.deviner(id_jeu, proposition).build_transaction({
                "from": adresse_b,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": gas_price
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key_b)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction de devinette envoyée avec hash : {tx_hash.hex()}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt["status"] == 1:
                print("✅ Proposition enregistrée.")
            else:
                print("❌ Échec de la proposition.")
        except Exception as e:
            print(f"Erreur lors de la proposition : {e}")

    def deviner_nombre_et_afficher_resultat(self, id_jeu, proposition, adresse_b, private_key_b):
        """Deviner un nombre et afficher le résultat"""
        try:
            # Vérifier d'abord s'il reste des tentatives
            tentatives_restantes = self.get_tentatives_restantes(id_jeu)
            if tentatives_restantes == 0:
                print("❌ Plus de tentatives restantes. Le jeu est terminé.")
                return True

            print(f"Proposition pour le jeu {id_jeu} : {proposition}")
            nonce = self.w3.eth.get_transaction_count(adresse_b)
            gas_price = self.w3.eth.gas_price

            tx = self.contract.functions.deviner(id_jeu, proposition).build_transaction({
                "from": adresse_b,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": gas_price
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key_b)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction de devinette envoyée avec hash : {tx_hash.hex()}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt["status"] == 1:
                print("✅ Proposition enregistrée.")
                try:
                    # Traiter les événements
                    logs_devine = self.contract.events.NombreDevine().process_receipt(receipt)
                    resultat = None
                    for log in logs_devine:
                        resultat = log['args']['resultat']
                        print(f"📣 Résultat : {resultat}")
                        if resultat == "Correct !":
                            print("🎉 Félicitations ! Vous avez deviné le nombre.")
                            return True

                    # Traiter les événements de fin de jeu
                    logs_termine = self.contract.events.JeuTermine().process_receipt(receipt)
                    for log in logs_termine:
                        message = log['args']['message']
                        print(f"🎮 {message}")
                        if "tentatives epuises" in message.lower():
                            print("❌ Perdu ! Vous avez épuisé toutes vos tentatives.")
                            return True

                    # Si le jeu continue
                    tentatives_restantes = self.get_tentatives_restantes(id_jeu)
                    if tentatives_restantes > 0:
                        print(f"Tentatives restantes : {tentatives_restantes}")
                    return False

                except Exception as e:
                    print(f"❌ Erreur lors du traitement des événements : {e}")
                    return False
            else:
                print("❌ La transaction a échoué.")
                return False
        except Exception as e:
            print(f"Erreur lors de la proposition : {e}")
            return False

    def reinitialiser_jeu(self, id_jeu, nouveau_nombre_secret, nouveau_tentatives_max, mise_a, private_key_a):
        """Réinitialiser un jeu"""
        try:
            print(f"Réinitialisation du jeu {id_jeu}...")
            adresse_a = self.w3.eth.account.from_key(private_key_a).address
            nonce = self.w3.eth.get_transaction_count(adresse_a)
            gas_price = self.w3.eth.gas_price

            tx = self.contract.functions.reinitialiserJeu(id_jeu, nouveau_nombre_secret, nouveau_tentatives_max).build_transaction({
                "from": adresse_a,
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
                print("❌ Échec de la réinitialisation.")
        except Exception as e:
            print(f"Erreur lors de la réinitialisation : {e}")

    def get_etat(self, id_jeu):
        """Obtenir l'état d'un jeu"""
        try:
            etat = self.contract.functions.getEtat(id_jeu).call()
            print(f"État du jeu {id_jeu} : {etat}")
            return etat
        except Exception as e:
            print(f"Erreur lors de la récupération de l'état : {e}")
            return None

    def get_tentatives_restantes(self, id_jeu):
        """Obtenir le nombre de tentatives restantes pour un jeu"""
        try:
            tentatives = self.contract.functions.getTentativesRestantes(id_jeu).call()
            print(f"Tentatives restantes pour le jeu {id_jeu} : {tentatives}")
            return tentatives
        except Exception as e:
            print(f"Erreur lors de la récupération des tentatives restantes : {e}")
            return None

    def lister_jeux(self):
        """Lister tous les jeux disponibles"""
        try:
            compteur_jeux = self.contract.functions.compteurJeux().call()
            print(f"Nombre total de jeux : {compteur_jeux}")
            for id_jeu in range(compteur_jeux):
                jeu = self.contract.functions.jeux(id_jeu).call()
                print(f"\nJeu ID : {id_jeu}")
                print(f"  Joueur A : {jeu[1]}")
                print(f"  Joueur B : {jeu[2]}")
                print(f"  Tentatives restantes : {jeu[4]}")
                print(f"  Mise du joueur A : {self.w3.from_wei(jeu[5], 'ether')} ETH")
                print(f"  Mise du joueur B : {self.w3.from_wei(jeu[6], 'ether')} ETH")
                print(f"  État : {'En cours' if jeu[7] == 1 else 'Terminé' if jeu[7] == 2 else 'En attente'}")
        except Exception as e:
            print(f"Erreur lors de la récupération des jeux : {e}")

    def lister_ids_jeux(self):
        """Lister uniquement les IDs des jeux disponibles sans joueur B enregistré"""
        try:
            ids = []
            compteur_jeux = self.contract.functions.compteurJeux().call()
            print(f"Nombre total de jeux : {compteur_jeux}")
            for id_jeu in range(compteur_jeux):
                jeu = self.contract.functions.jeux(id_jeu).call()
                if jeu[7] == 1 and jeu[2] == "0x0000000000000000000000000000000000000000":  # Vérifie si le jeu est "En cours" et sans joueur B
                    ids.append(id_jeu)
            print(f"IDs des jeux disponibles sans joueur B : {ids}")
            return ids
        except Exception as e:
            print(f"Erreur lors de la récupération des IDs des jeux : {e}")
            return []

def main():
    # Charger les informations du contrat et des joueurs
    contract_address = "0x4C41189BfEc8beC2a73e5D5BD5bFD80139E695aB"
    abi_path = "Projet/abi_V3.json"
    private_key_a = os.getenv("PRIVATE_KEY_A")
    private_key_b = os.getenv("PRIVATE_KEY_B")
    adresse_a = os.getenv("ADRESSE_A")
    adresse_b = os.getenv("ADRESSE_B")

    jeu = DevineNombreGeneriqueInterface(contract_address, abi_path)

    def afficher_menu():
        """Afficher les choix du menu principal"""
        print("\n--- Menu Principal ---")
        print("1. Créer un nouveau jeu")
        print("2. Participer à un jeu et deviner un nombre")
        print("3. Réinitialiser un jeu")
        print("4. Lister tous les jeux disponibles")
        print("0. Quitter")

    afficher_menu()

    while True:
        choix = input("\nEntrez votre choix : ")
        if choix == "1":
            try:
                nombre_secret = int(input("Entrez le nombre secret (entre 1 et 100) : "))
                tentatives_max = int(input("Entrez le nombre maximum de tentatives : "))
                mise_a = float(input("Entrez la mise en ETH : "))
                jeu.creer_jeu(nombre_secret, tentatives_max, mise_a, private_key_a)
            except Exception as e:
                print(f"Erreur lors de la création du jeu : {e}")
        elif choix == "2":
            try:
                ids_disponibles = jeu.lister_ids_jeux()
                if not ids_disponibles:
                    print("Aucun jeu disponible pour participer.")
                    continue
                id_jeu = int(input("Entrez l'ID du jeu auquel vous voulez participer : "))
                if id_jeu not in ids_disponibles:
                    print("ID de jeu invalide. Veuillez réessayer.")
                    continue
                mise_b = float(input("Entrez la mise en ETH : "))
                jeu.participer(id_jeu, mise_b, adresse_b, private_key_b)
                print("\nDébut du jeu - Tentez de deviner le nombre!")
                while True:
                    proposition = input("\nEntrez votre proposition (ou 'exit' pour quitter) : ")
                    if proposition.lower() == "exit":
                        print("Fin du jeu.")
                        break
                    try:
                        proposition = int(proposition)
                        if jeu.deviner_nombre_et_afficher_resultat(id_jeu, proposition, adresse_b, private_key_b):
                            break  # Sort de la boucle si le jeu est terminé
                    except ValueError:
                        print("❌ Veuillez entrer un nombre valide.")
                    except Exception as e:
                        print(f"❌ Erreur lors de la tentative : {e}")
            except Exception as e:
                print(f"Erreur lors de la participation : {e}")
        elif choix == "3":
            try:
                id_jeu = int(input("Entrez l'ID du jeu : "))
                nouveau_nombre_secret = int(input("Entrez le nouveau nombre secret (entre 1 et 100) : "))
                nouveau_tentatives_max = int(input("Entrez le nouveau nombre maximum de tentatives : "))
                mise_a = float(input("Entrez la nouvelle mise en ETH : "))
                jeu.reinitialiser_jeu(id_jeu, nouveau_nombre_secret, nouveau_tentatives_max, mise_a, private_key_a)
            except Exception as e:
                print(f"Erreur lors de la réinitialisation : {e}")
        elif choix == "4":
            jeu.lister_jeux()
        elif choix == "0":
            print("Fin du programme.")
            break
        else:
            print("Choix invalide. Veuillez réessayer.")

        afficher_menu()  # Rappeler les choix du menu après chaque saisie

if __name__ == "__main__":
    main()