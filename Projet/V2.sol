// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DevineNombreAvecMise {
    uint256 private nombreSecret;
    address public joueurA;
    address public joueurB;
    uint256 public tentativesMax;
    uint256 public tentativesRestantes;
    uint256 public miseA;
    uint256 public miseB;

    uint256 public constant MIN_NOMBRE = 1;
    uint256 public constant MAX_NOMBRE = 100;

    enum Etat { EnAttente, EnCours, Termine }
    Etat public etat;

    event NombreDevine(uint256 proposition, string resultat);
    event JeuTermine(string message);
    event MisePlace(address joueur, uint256 montant);
    event JoueurBAttribue(address joueurB);
    event JeuReinitialise(string message);

    constructor(uint256 _nombreSecret, uint256 _tentativesMax) payable {
        require(_nombreSecret >= MIN_NOMBRE && _nombreSecret <= MAX_NOMBRE, 
            "Le nombre doit etre entre 1 et 100");
        require(_tentativesMax > 0, "Le nombre de tentatives doit etre positif");
        require(msg.value > 0, "Le joueur A doit placer une mise");
        joueurA = msg.sender;
        nombreSecret = _nombreSecret;
        tentativesMax = _tentativesMax;
        tentativesRestantes = _tentativesMax;
        miseA = msg.value;
        etat = Etat.EnCours;
    }

    function participer() external payable {
        require(etat == Etat.EnCours, "Le jeu est termine");
        require(msg.value > 0, "Une mise est requise");
        require(msg.sender != joueurA, "Le joueur A ne peut pas participer");
        require(joueurB == address(0), "Un joueur B existe deja");
        require(msg.value >= miseA, "La mise doit etre au moins egale a celle du joueur A");

        joueurB = msg.sender;
        miseB = msg.value;

        emit JoueurBAttribue(joueurB);
        emit MisePlace(joueurB, miseB);

        // Ajoutez des logs pour déboguer
        emit JeuTermine(string(abi.encodePacked("Participation réussie : ", msg.sender)));
        emit JeuTermine(string(abi.encodePacked("Mise reçue : ", uint2str(msg.value))));
        emit JeuTermine(string(abi.encodePacked("Mise minimale requise : ", uint2str(miseA))));
    }

    // Fonction utilitaire pour convertir uint en string
    function uint2str(uint _i) internal pure returns (string memory) {
        if (_i == 0) {
            return "0";
        }
        uint j = _i;
        uint len;
        while (j != 0) {
            len++;
            j /= 10;
        }
        bytes memory bstr = new bytes(len);
        uint k = len;
        while (_i != 0) {
            k = k - 1;
            uint8 temp = (48 + uint8(_i - _i / 10 * 10));
            bytes1 b1 = bytes1(temp);
            bstr[k] = b1;
            _i /= 10;
        }
        return string(bstr);
    }

    function deviner(uint256 _proposition) public {
        require(msg.sender == joueurB, "Seul le joueur B peut deviner");
        require(etat == Etat.EnCours, "Le jeu est termine");
        require(tentativesRestantes > 0, "Tentatives epuises");

        if (_proposition < nombreSecret) {
            tentativesRestantes--;
            emit NombreDevine(_proposition, "Plus petit");
        } else if (_proposition > nombreSecret) {
            tentativesRestantes--;
            emit NombreDevine(_proposition, "Plus grand");
        } else {
            etat = Etat.Termine;
            emit NombreDevine(_proposition, "Correct !");
            payable(joueurB).transfer(miseA + miseB);
            emit JeuTermine("Le joueur B a devine le nombre !");
            _reinitialiserAutomatiquement(); // Redémarrer automatiquement avec les mêmes valeurs
        }

        if (tentativesRestantes == 0) {
            etat = Etat.Termine;
            emit JeuTermine("Le jeu est termine. Tentatives epuises.");
            _reinitialiserAutomatiquement(); // Redémarrer automatiquement avec les mêmes valeurs
        }
    }

    function _reinitialiserAutomatiquement() internal {
        // Réinitialiser les variables du jeu avec les mêmes valeurs
        tentativesRestantes = tentativesMax;
        miseB = 0;
        joueurB = address(0);
        etat = Etat.EnCours;

        emit JeuReinitialise("Le jeu a été automatiquement réinitialisé avec le même nombre secret.");
    }

    function reinitialiserJeu(uint256 _nouveauNombreSecret, uint256 _nouveauTentativesMax) public payable {
        require(msg.sender == joueurA, "Seul le joueur A peut reinitialiser le jeu");
        require(etat == Etat.Termine, "Le jeu doit etre termine pour etre reinitialise");
        require(msg.value > 0, "Le joueur A doit placer une nouvelle mise");

        nombreSecret = _nouveauNombreSecret;
        tentativesMax = _nouveauTentativesMax;
        tentativesRestantes = _nouveauTentativesMax;
        miseA = msg.value;
        miseB = 0;
        etat = Etat.EnCours;
        joueurB = address(0);

        emit JeuReinitialise("Le jeu a ete reinitialise.");
    }

    function recupererMise() external {
        require(msg.sender == joueurA, "Seul le joueur A peut recuperer sa mise");
        require(joueurB == address(0), "Le joueur B est deja enregistre");
        require(etat == Etat.EnCours, "Le jeu n'est pas en cours");
        
        etat = Etat.Termine;
        _envoyerGain(joueurA, miseA);
        emit JeuTermine("Mise recuperee par le joueur A");
    }

    function getEtat() public view returns (string memory) {
        if (etat == Etat.EnCours) {
            return "En cours";
        } else if (etat == Etat.Termine) {
            return "Termine";
        } else {
            return "En attente";
        }
    }

    function getTentativesRestantes() public view returns (uint256) {
        return tentativesRestantes;
    }

    function getResultat(uint256 _proposition) public view returns (string memory) {
        if (_proposition < nombreSecret) {
            return "Plus petit";
        } else if (_proposition > nombreSecret) {
            return "Plus grand";
        } else {
            return "Correct !";
        }
    }

    function getMiseMinimale() external view returns (uint256) {
        return miseA;
    }

    function estJeuActif() external view returns (bool) {
        return etat == Etat.EnCours && joueurB != address(0);
    }

    function _envoyerGain(address destinataire, uint256 montant) internal {
        (bool success, ) = destinataire.call{value: montant}("");
        require(success, "Echec du transfert");
    }
}

