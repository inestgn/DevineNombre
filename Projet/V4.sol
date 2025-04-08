// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DevineNombreConfidentiel {
    enum Etat { EnAttente, EnCours, Termine }
    enum Reponse { Aucune, PlusPetit, PlusGrand, Egal }

    struct Proposition {
        uint256 valeur;
        Reponse reponseA;
        bool validee;
    }

    struct Jeu {
        bytes32 nombreHashe;     // Hash du nombre secret + sel
        address joueurA;
        address joueurB;
        uint256 tentativesMax;
        uint256 tentativesRestantes;
        uint256 miseA;
        uint256 miseB;
        Etat etat;
        bool nombreRevele;
        mapping(uint256 => Proposition) propositions;
        uint256 nbPropositions;
    }

    mapping(uint256 => Jeu) public jeux;
    uint256 public compteurJeux;

    event JeuCree(uint256 idJeu, address joueurA, uint256 tentativesMax);
    event NombrePropose(uint256 idJeu, uint256 proposition);
    event ReponseA(uint256 idJeu, uint256 proposition, string reponse);
    event NombreRevele(uint256 idJeu, uint256 nombreSecret, uint256 sel);
    event JeuTermine(uint256 idJeu, string message);
    event MisePlace(uint256 idJeu, address joueur, uint256 montant);

    function creerJeu(bytes32 _nombreHashe, uint256 _tentativesMax) public payable {
        require(_tentativesMax > 0, "Le nombre de tentatives doit etre superieur a 0");
        require(msg.value > 0, "Une mise initiale est requise");

        uint256 idJeu = compteurJeux++;
        Jeu storage jeu = jeux[idJeu];
        jeu.nombreHashe = _nombreHashe;
        jeu.joueurA = msg.sender;
        jeu.tentativesMax = _tentativesMax;
        jeu.tentativesRestantes = _tentativesMax;
        jeu.miseA = msg.value;
        jeu.etat = Etat.EnCours;
        jeu.nombreRevele = false;

        emit JeuCree(idJeu, msg.sender, _tentativesMax);
    }

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

    function proposer(uint256 _idJeu, uint256 _proposition) public {
        Jeu storage jeu = jeux[_idJeu];
        require(msg.sender == jeu.joueurB, "Seul le joueur B peut proposer");
        require(jeu.etat == Etat.EnCours, "Le jeu n'est pas en cours");
        require(jeu.tentativesRestantes > 0, "Plus de tentatives restantes");

        uint256 indexProposition = jeu.nbPropositions++;
        jeu.propositions[indexProposition] = Proposition({
            valeur: _proposition,
            reponseA: Reponse.Aucune,
            validee: false
        });
        
        emit NombrePropose(_idJeu, _proposition);
    }

    function repondre(uint256 _idJeu, uint256 _indexProposition, Reponse _reponse) public {
        Jeu storage jeu = jeux[_idJeu];
        require(msg.sender == jeu.joueurA, "Seul le joueur A peut repondre");
        require(jeu.etat == Etat.EnCours, "Le jeu n'est pas en cours");
        require(_indexProposition < jeu.nbPropositions, "Proposition invalide");
        require(!jeu.propositions[_indexProposition].validee, "Reponse deja donnee");

        Proposition storage prop = jeu.propositions[_indexProposition];
        prop.reponseA = _reponse;
        prop.validee = true;
        jeu.tentativesRestantes--;

        string memory reponseStr;
        if (_reponse == Reponse.PlusPetit) reponseStr = "Plus petit";
        else if (_reponse == Reponse.PlusGrand) reponseStr = "Plus grand";
        else if (_reponse == Reponse.Egal) {
            reponseStr = "Correct !";
            jeu.etat = Etat.Termine;
            payable(jeu.joueurB).transfer(jeu.miseA + jeu.miseB);
        }

        emit ReponseA(_idJeu, prop.valeur, reponseStr);

        if (jeu.tentativesRestantes == 0 && jeu.etat != Etat.Termine) {
            jeu.etat = Etat.Termine;
            payable(jeu.joueurA).transfer(jeu.miseA + jeu.miseB);
            emit JeuTermine(_idJeu, "Tentatives epuisees");
        }
    }

    function revelerNombre(uint256 _idJeu, uint256 _nombreSecret, uint256 _sel) public {
        Jeu storage jeu = jeux[_idJeu];
        require(msg.sender == jeu.joueurA, "Seul le joueur A peut reveler");
        require(jeu.etat == Etat.Termine, "Le jeu doit etre termine");
        require(!jeu.nombreRevele, "Nombre deja revele");

        bytes32 hash = keccak256(abi.encodePacked(_nombreSecret, _sel));
        require(hash == jeu.nombreHashe, "Le nombre revele ne correspond pas au hash");

        jeu.nombreRevele = true;
        emit NombreRevele(_idJeu, _nombreSecret, _sel);

        // Vérifier que les réponses étaient correctes
        for (uint256 i = 0; i < jeu.nbPropositions; i++) {
            Proposition storage prop = jeu.propositions[i];
            if (prop.validee) {
                Reponse reponseAttendue;
                if (prop.valeur < _nombreSecret) reponseAttendue = Reponse.PlusPetit;
                else if (prop.valeur > _nombreSecret) reponseAttendue = Reponse.PlusGrand;
                else reponseAttendue = Reponse.Egal;

                require(prop.reponseA == reponseAttendue, "Reponse incorrecte detectee");
            }
        }
    }

    // Obtenir l'état d'un jeu
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

    // Obtenir le nombre de tentatives restantes
    function getTentativesRestantes(uint256 _idJeu) public view returns (uint256) {
        return jeux[_idJeu].tentativesRestantes;
    }
}

