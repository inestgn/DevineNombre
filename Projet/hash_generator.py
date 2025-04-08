import random
from web3 import Web3

def generer_hash():
    w3 = Web3()
    
    # Saisie du nombre secret
    while True:
        try:
            nombre_secret = int(input("Entrez votre nombre secret (entre 1 et 100) : "))
            if 1 <= nombre_secret <= 100:
                break
            print("Le nombre doit être entre 1 et 100")
        except ValueError:
            print("Veuillez entrer un nombre valide")

    # Génération du sel aléatoire
    sel = random.randint(1, 1000000)
    
    # Calcul du hash
    hash_nombre = w3.solidity_keccak(['uint256', 'uint256'], [nombre_secret, sel])
    
    print("\n=== GARDEZ CES INFORMATIONS EN LIEU SÛR ===")
    print(f"Nombre secret : {nombre_secret}")
    print(f"Sel : {sel}")
    print(f"\nHash à utiliser dans le jeu : {hash_nombre.hex()}")
    print("\nNE PARTAGEZ PAS LE NOMBRE SECRET ET LE SEL !")
    print("Conservez-les pour la révélation finale.")

if __name__ == "__main__":
    generer_hash()
