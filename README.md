# Jeu "Devine Nombre" sur Ethereum

Ce projet implémente un jeu de devinettes de nombres sur la blockchain Ethereum, avec plusieurs versions évolutives.

## Versions

### Version 1 : Jeu de base
- Joueur A choisit un nombre entre 1-100
- Joueur B tente de deviner
- Nombre limité de tentatives
- Smart contract basique
- Le nombre a deviner est 42
- Le jeu se réinitialise une fois toutes les tentatives échouées

### Version 2 : Jeu avec Mises
- Ajout de mises en ETH
- Le gagnant remporte la totalité des mises
- Réinitialisation automatique du jeu
- Gestion des mises minimales
- Le nombre a deviner est 44
- La partie est réinitialisée à chaque fois qu'on lance le programme


### Version 3 : Contrat Générique
- Support de multiples parties simultanées
- Système d'ID pour les jeux
- Gestion des mises par partie
- Liste des jeux disponibles
Attention !  Au debut, il n'y a pas de partie initialisée donc vous ne pourrez pas entrer dans une partie, commencer par créer un nouveau jeu.  

Dans l'option 2 du menu pour participer à un jeu, vous aurez la liste des id de jeu dans lesquels vous pouvez entrer, soit ceux qui sont encore en attente de deuxième joueur

### Version 4 : Jeu Confidentiel
- Hash du nombre secret
- Vérification des réponses de A
- Révélation du nombre à la fin
- Protection contre la triche
- Attention a bien écrire plus_petit / plus_grand / egal (ne pas oublier le _)

## Installation
1. Cloner le repository
2. Installer les dépendances : `pip install -r requirements.txt`
3. Configurer le fichier `.env` avec vos clés

## Utilisation
1. Démarrer la version souhaitée :
   ```bash
   python dapp_v1.py  # Version 1
   python dapp_v2.py  # Version 2
   python dapp_v3.py  # Version 3
   python dapp_v4.py  # Version 4 (avec hash_generator.py)
   ```

2. Pour la V4, générer d'abord le hash :
   ```bash
   python hash_generator.py
   ```

   Si besoin, voici deja un hash : 01ea8777cc3cf41c1ff6ce95e88bf27598ce5b9fbd8b80c2e7d2cd49a1d97ac7
   et un sel : 651123
   correspondant au nombre 45

Certaines transactions peuvent planter ou mettre du temps avant d'être bien envoyées, dans ce cas la attendre et si besoin relancer, toutes les fonctionnalités implémentées ont été testées et validées.  

## Configuration requise
- Python 3.8+
- Web3.py
- Compte Ethereum avec des fonds sur Sepolia
- Clés privées configurées dans .env a modifier eventuellement dans les fichiers dapp