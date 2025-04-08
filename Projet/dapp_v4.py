import os
import json
import warnings
from web3 import Web3
import random
from dotenv import load_dotenv

# Ignorer les avertissements spécifiques de Web3
warnings.filterwarnings('ignore', message='.*MismatchedABI.*')

# Charger les variables d'environnement
load_dotenv()

class DevineNombreConfidentielInterface:
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

    def creer_jeu(self, nombre_hache, tentatives_max, mise_a, private_key_a):
        """Créer un nouveau jeu avec un hash fourni"""
        try:
            print("Création d'un nouveau jeu...")
            adresse_a = self.w3.eth.account.from_key(private_key_a).address
            nonce = self.w3.eth.get_transaction_count(adresse_a)
            gas_price = self.w3.eth.gas_price

            tx = self.contract.functions.creerJeu(nombre_hache, tentatives_max).build_transaction({
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
        except Exception as e:
            print(f"Erreur lors de la participation : {e}")

    def proposer_nombre(self, id_jeu, proposition, adresse_b, private_key_b):
        """Proposer un nombre pour le jeu"""
        try:
            print(f"Envoi de la proposition : {proposition}")
            nonce = self.w3.eth.get_transaction_count(adresse_b)
            gas_price = self.w3.eth.gas_price

            tx = self.contract.functions.proposer(id_jeu, proposition).build_transaction({
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
                print("✅ Proposition enregistrée.")
                return True
            else:
                print("❌ La transaction a échoué.")
                return False
        except Exception as e:
            print(f"Erreur lors de la proposition : {e}")
            return False

    def repondre(self, id_jeu, index_proposition, reponse, adresse_a, private_key_a):
        """Répondre à une proposition en tant que joueur A"""
        try:
            nonce = self.w3.eth.get_transaction_count(adresse_a)
            gas_price = self.w3.eth.gas_price

            # Convertir la réponse en enum (0: Aucune, 1: PlusPetit, 2: PlusGrand, 3: Egal)
            reponse_enum = {"plus_petit": 1, "plus_grand": 2, "egal": 3}[reponse.lower()]

            tx = self.contract.functions.repondre(id_jeu, index_proposition, reponse_enum).build_transaction({
                "from": adresse_a,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": gas_price
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key_a)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction de réponse envoyée avec hash : {tx_hash.hex()}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt["status"] == 1:
                print("✅ Réponse enregistrée.")
                return True
            else:
                print("❌ La réponse a échoué.")
                return False
        except Exception as e:
            print(f"Erreur lors de la réponse : {e}")
            return False

    def reveler_nombre(self, id_jeu, adresse_a, private_key_a):
        """Révéler le nombre secret et le sel à la fin du jeu"""
        try:
            if not hasattr(self, 'dernier_nombre_secret') or not hasattr(self, 'dernier_sel'):
                print("❌ Nombre secret ou sel non disponible.")
                return False

            nonce = self.w3.eth.get_transaction_count(adresse_a)
            gas_price = self.w3.eth.gas_price

            tx = self.contract.functions.revelerNombre(
                id_jeu, 
                self.dernier_nombre_secret, 
                self.dernier_sel
            ).build_transaction({
                "from": adresse_a,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": gas_price
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key_a)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction de révélation envoyée avec hash : {tx_hash.hex()}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt["status"] == 1:
                print("✅ Nombre secret révélé avec succès.")
                return True
            else:
                print("❌ Échec de la révélation du nombre.")
                return False
        except Exception as e:
            print(f"Erreur lors de la révélation du nombre : {e}")
            return False

    def reveler_nombre_verification(self, id_jeu, nombre_secret, sel, adresse_a, private_key_a):
        """Révéler et vérifier le nombre secret à la fin du jeu"""
        try:
            print(f"Révélation du nombre secret {nombre_secret} avec le sel {sel}...")
            nonce = self.w3.eth.get_transaction_count(adresse_a)
            gas_price = self.w3.eth.gas_price

            tx = self.contract.functions.revelerNombre(id_jeu, nombre_secret, sel).build_transaction({
                "from": adresse_a,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": gas_price
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key_a)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction de révélation envoyée avec hash : {tx_hash.hex()}")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt["status"] == 1:
                # Traiter les événements de révélation
                try:
                    logs_revele = self.contract.events.NombreRevele().process_receipt(receipt)
                    for log in logs_revele:
                        print(f"✅ Nombre secret révélé : {log['args']['nombreSecret']}")
                        print(f"✅ Sel utilisé : {log['args']['sel']}")
                    return True
                except Exception as e:
                    print(f"❌ Erreur lors du traitement des événements : {e}")
                    return False
            else:
                print("❌ La transaction a échoué.")
                return False
        except Exception as e:
            print(f"❌ Erreur lors de la révélation : {e}")
            return False

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
                # Vérifier si le jeu est en cours et sans joueur B
                if jeu[7] == 1 and jeu[2] == "0x0000000000000000000000000000000000000000":
                    ids.append(id_jeu)
            print(f"IDs des jeux disponibles sans joueur B : {ids}")
            return ids
        except Exception as e:
            print(f"Erreur lors de la récupération des IDs des jeux : {e}")
            return []

    def get_etat(self, id_jeu):
        """Obtenir l'état d'un jeu"""
        try:
            etat = self.contract.functions.getEtat(id_jeu).call()
            return etat
        except Exception as e:
            print(f"Erreur lors de la récupération de l'état : {e}")
            return None

    def get_tentatives_restantes(self, id_jeu):
        """Obtenir le nombre de tentatives restantes pour un jeu"""
        try:
            tentatives = self.contract.functions.getTentativesRestantes(id_jeu).call()
            return tentatives
        except Exception as e:
            print(f"Erreur lors de la récupération des tentatives restantes : {e}")
            return None

def main():
    # Charger les informations du contrat et des joueurs
    contract_address = "0xE2A979be73E3574591Bc68A2755a9f8fea7a0315"
    abi_path = "Projet/abi_V4.json"
    private_key_a = os.getenv("PRIVATE_KEY_A")
    private_key_b = os.getenv("PRIVATE_KEY_B")
    adresse_a = os.getenv("ADRESSE_A")
    adresse_b = os.getenv("ADRESSE_B")

    jeu = DevineNombreConfidentielInterface(contract_address, abi_path)

    def afficher_menu():
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
                print("\nUtilisez d'abord hash_generator.py pour générer le hash de votre nombre secret")
                nombre_hache = input("Entrez le hash généré : ")
                if not nombre_hache.startswith("0x"):
                    nombre_hache = "0x" + nombre_hache
                tentatives_max = int(input("Entrez le nombre maximum de tentatives : "))
                mise_a = float(input("Entrez la mise en ETH : "))
                jeu.creer_jeu(nombre_hache, tentatives_max, mise_a, private_key_a)
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

                index_proposition = 0
                while True:
                    tentatives = jeu.get_tentatives_restantes(id_jeu)
                    if tentatives == 0:
                        print("❌ Plus de tentatives restantes. Le jeu est terminé.")
                        break

                    print(f"\nTentatives restantes : {tentatives}")
                    proposition = input("\nEntrez votre proposition (ou 'exit' pour quitter) : ")
                    if proposition.lower() == "exit":
                        print("Fin du jeu.")
                        break

                    try:
                        proposition = int(proposition)
                        if jeu.proposer_nombre(id_jeu, proposition, adresse_b, private_key_b):
                            print("\nJoueur A - C'est à vous de répondre.")
                            reponse = input("Entrez votre réponse (plus_petit/plus_grand/egal) : ")
                            
                            if jeu.repondre(id_jeu, index_proposition, reponse, adresse_a, private_key_a):
                                etat = jeu.get_etat(id_jeu)
                                if reponse == "egal" or etat == "Termine":
                                    if reponse == "egal":
                                        print("🎉 Félicitations ! Le nombre a été deviné.")
                                    else:
                                        print("❌ Plus de tentatives. Le jeu est terminé.")
                                    
                                    print("\nJoueur A - Vous devez maintenant révéler le nombre secret pour vérification.")
                                    nombre_secret = int(input("Entrez le nombre secret : "))
                                    sel = int(input("Entrez le sel utilisé : "))
                                    
                                    if jeu.reveler_nombre_verification(id_jeu, nombre_secret, sel, adresse_a, private_key_a):
                                        print("✅ Nombre secret révélé et vérifié avec succès.")
                                        print("✅ Les réponses données pendant le jeu étaient correctes.")
                                    else:
                                        print("❌ Échec de la vérification. Les réponses de A étaient incorrectes.")
                                    break
                            index_proposition += 1
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
                # TODO: Implémenter la réinitialisation pour V4
                print("Fonctionnalité non disponible dans cette version.")
            except Exception as e:
                print(f"Erreur lors de la réinitialisation : {e}")

        elif choix == "4":
            jeu.lister_jeux()

        elif choix == "0":
            print("Fin du programme.")
            break

        else:
            print("Choix invalide. Veuillez réessayer.")

        afficher_menu()

if __name__ == "__main__":
    main()
