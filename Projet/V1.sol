// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

contract DevineNombre {
    uint256 private nombreSecret; // Nombre secret choisi par le joueur A
    address public joueurA; // Adresse du joueur A
    address public joueurB; // Adresse du joueur B
    uint256 public tentativesMax; // Nombre maximum de tentatives
    uint256 public tentativesRestantes; // Tentatives restantes

    enum Etat { EnAttente, EnCours, Termine }
    Etat public etat; // État du jeu

    // Événements pour notifier les actions
    event NombreDevine(uint256 proposition, string resultat);
    event JeuTermine(string message);

    // Constructeur pour initialiser le contrat
    constructor(uint256 _nombreSecret, uint256 _tentativesMax) {
        joueurA = msg.sender; // Le joueur A déploie le contrat
        nombreSecret = _nombreSecret; // Nombre secret
        tentativesMax = _tentativesMax; // Limite de tentatives
        tentativesRestantes = _tentativesMax; // Initialiser les tentatives restantes
        etat = Etat.EnCours; // État du jeu
    }

    // Fonction pour deviner le nombre
    function deviner(uint256 _proposition) public {
        if (joueurB == address(0)) {
            require(msg.sender != joueurA, "Erreur: Le joueur A ne peut pas deviner");
            joueurB = msg.sender; // Enregistre le premier joueur comme joueur B
        }
        require(msg.sender == joueurB, "Erreur: Seul le joueur B peut deviner");
        require(etat == Etat.EnCours, "Erreur: Le jeu est termine");
        require(tentativesRestantes > 0, "Erreur: Tentatives epuises");

        // Comparer la proposition avec le nombre secret
        if (_proposition < nombreSecret) {
            tentativesRestantes--;
            emit NombreDevine(_proposition, "Plus petit");
        } else if (_proposition > nombreSecret) {
            tentativesRestantes--;
            emit NombreDevine(_proposition, "Plus grand");
        } else {
            etat = Etat.Termine;
            emit NombreDevine(_proposition, "Correct !");
            emit JeuTermine("Le joueur B a devine le nombre !");
        }

        // Vérifier si les tentatives sont épuisées
        if (tentativesRestantes == 0) {
            etat = Etat.Termine;
            emit JeuTermine("Le jeu est termine. Tentatives epuises.");
        }
    }

    // Fonction pour obtenir l'état du jeu
    function getEtat() public view returns (string memory) {
        if (etat == Etat.EnCours) {
            return "En cours";
        } else if (etat == Etat.Termine) {
            return "Termine"; 
        } else {
            return "En attente"; // Ajouter un état pour le cas "EnAttente"
        }
    }

    // Fonction pour obtenir le nombre de tentatives restantes
    function getTentativesRestantes() public view returns (uint256) {
        return tentativesRestantes;
    }

    // Fonction pour réinitialiser le jeu
    function reinitialiserJeu(uint256 _nouveauNombreSecret, uint256 _nouveauTentativesMax) public {
        require(msg.sender == joueurA, "Seul le joueur A peut reinitialiser le jeu");
        require(etat == Etat.Termine, "Le jeu doit etre termine pour etre reinitialise");

        nombreSecret = _nouveauNombreSecret;
        tentativesMax = _nouveauTentativesMax;
        tentativesRestantes = _nouveauTentativesMax;
        etat = Etat.EnCours;
        joueurB = address(0); // Réinitialiser le joueur B

        emit JeuTermine("Le jeu a ete reinitialise.");
    }
}
