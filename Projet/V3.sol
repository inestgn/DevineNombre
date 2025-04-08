// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DevineNombreGenerique {
    enum Etat { EnAttente, EnCours, Termine } // État du jeu

    struct Jeu {
        uint256 nombreSecret; // Nombre secret choisi par le joueur A
        address joueurA; // Adresse du joueur A
        address joueurB; // Adresse du joueur B
        uint256 tentativesMax; // Nombre maximum de tentatives
        uint256 tentativesRestantes; // Tentatives restantes
        uint256 miseA; // Mise du joueur A
        uint256 miseB; // Mise du joueur B
        Etat etat; // État du jeu
    }

    mapping(uint256 => Jeu) public jeux; // Mapping pour stocker les jeux
    uint256 public compteurJeux; // Compteur pour identifier les jeux

    event JeuCree(uint256 idJeu, address joueurA, uint256 tentativesMax);
    event NombreDevine(uint256 idJeu, uint256 proposition, string resultat);
    event JeuTermine(uint256 idJeu, string message);
    event MisePlace(uint256 idJeu, address joueur, uint256 montant);

    // Fonction pour créer un nouveau jeu
    function creerJeu(uint256 _nombreSecret, uint256 _tentativesMax) public payable {
        require(_nombreSecret >= 1 && _nombreSecret <= 100, "Le nombre doit etre entre 1 et 100");
        require(_tentativesMax > 0, "Le nombre de tentatives doit etre superieur a 0");
        require(msg.value > 0, "Une mise initiale est requise");

        jeux[compteurJeux] = Jeu({
            nombreSecret: _nombreSecret,
            joueurA: msg.sender,
            joueurB: address(0),
            tentativesMax: _tentativesMax,
            tentativesRestantes: _tentativesMax,
            miseA: msg.value,
            miseB: 0,
            etat: Etat.EnCours
        });

        emit JeuCree(compteurJeux, msg.sender, _tentativesMax);
        compteurJeux++;
    }

    // Fonction pour que le joueur B participe
    function participer(uint256 _idJeu) public payable {
        Jeu storage jeu = jeux[_idJeu];
        require(jeu.etat == Etat.EnCours, "Le jeu n'est pas en cours");
        require(jeu.joueurB == address(0), "Un joueur B est deja enregistre");
        require(msg.sender != jeu.joueurA, "Le joueur A ne peut pas etre le joueur B");
        require(msg.value >= jeu.miseA, "La mise doit etre au moins egale a celle du joueur A");

        jeu.joueurB = msg.sender;
        jeu.miseB = msg.value;

        emit MisePlace(_idJeu, msg.sender, msg.value);
    }

    // Fonction pour deviner le nombre
    function deviner(uint256 _idJeu, uint256 _proposition) public {
        Jeu storage jeu = jeux[_idJeu];
        require(msg.sender == jeu.joueurB, "Seul le joueur B peut deviner");
        require(jeu.etat == Etat.EnCours, "Le jeu n'est pas en cours");
        require(jeu.tentativesRestantes > 0, "Tentatives epuises");

        if (_proposition < jeu.nombreSecret) {
            jeu.tentativesRestantes--;
            emit NombreDevine(_idJeu, _proposition, "Plus petit");
        } else if (_proposition > jeu.nombreSecret) {
            jeu.tentativesRestantes--;
            emit NombreDevine(_idJeu, _proposition, "Plus grand");
        } else {
            jeu.etat = Etat.Termine;
            emit NombreDevine(_idJeu, _proposition, "Correct !");
            payable(jeu.joueurB).transfer(jeu.miseA + jeu.miseB);
            emit JeuTermine(_idJeu, "Le joueur B a devine le nombre !");
        }

        if (jeu.tentativesRestantes == 0 && jeu.etat != Etat.Termine) {
            jeu.etat = Etat.Termine;
            emit JeuTermine(_idJeu, "Le jeu est termine. Tentatives epuises.");
        }
    }

    // Fonction pour réinitialiser un jeu
    function reinitialiserJeu(uint256 _idJeu, uint256 _nouveauNombreSecret, uint256 _nouveauTentativesMax) public payable {
        Jeu storage jeu = jeux[_idJeu];
        require(msg.sender == jeu.joueurA, "Seul le joueur A peut reinitialiser le jeu");
        require(jeu.etat == Etat.Termine, "Le jeu doit etre termine pour etre reinitialise");
        require(msg.value > 0, "Une nouvelle mise est requise");
        require(_nouveauNombreSecret >= 1 && _nouveauNombreSecret <= 100, "Le nombre doit etre entre 1 et 100");
        require(_nouveauTentativesMax > 0, "Le nombre de tentatives doit etre superieur a 0");

        jeu.nombreSecret = _nouveauNombreSecret;
        jeu.tentativesMax = _nouveauTentativesMax;
        jeu.tentativesRestantes = _nouveauTentativesMax;
        jeu.miseA = msg.value;
        jeu.miseB = 0;
        jeu.joueurB = address(0);
        jeu.etat = Etat.EnCours;

        emit JeuTermine(_idJeu, "Le jeu a ete reinitialise.");
    }

    // Fonction pour obtenir l'état d'un jeu
    function getEtat(uint256 _idJeu) public view returns (string memory) {
        Jeu storage jeu = jeux[_idJeu];
        if (jeu.etat == Etat.EnCours) {
            return "En cours";
        } else if (jeu.etat == Etat.Termine) {
            return "Termine";
        } else {
            return "En attente";
        }
    }

    // Fonction pour obtenir le nombre de tentatives restantes
    function getTentativesRestantes(uint256 _idJeu) public view returns (uint256) {
        return jeux[_idJeu].tentativesRestantes;
    }
}
