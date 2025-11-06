# Cahier des Charges

## Projet TS341 - Détection de drones

**Projet :** Détection de drones à partir de différentes sources vidéos  
**Client / Tuteur :**  
- Sébastien Delpeuch : s.delpeuch@catie.fr  
- Clément Pinet : c.pinet@catie.fr  

**Date de début de projet :** Novembre 2025  

**Équipe :**  
- ROBLIN Pauline  
- BASTIEN Hugo  
- ROUAULT Olivier  
- LARRAGUETA César  

**Classe :** 3A - Spécialité Robotique et Apprentissage

---

### 1. Description de la compréhension du besoin
L’utilisation des drones civils se développe rapidement, mais elle comporte des risques pour la sécurité et la vie privée. Il est donc crucial de pouvoir détecter et identifier les drones non autorisés sur certaines zones, à l'aide de différents types de caméras de surveillance. 

Dans ce contexte, une société spécialisée dans la protection de sites sensibles a sollicité le CATIE pour concevoir un système capable de repérer les drones à partir de flux vidéo provenant de différents types de caméras.

Le projet a donc pour objectif de mettre en place un dispositif qui devra permettre la détection d’un modèle de drone unique dans plusieurs situations :  
- à diverses altitudes  
- à différentes distances par rapport à la caméra  
- sous des conditions d’éclairage variées  
- avec des caméras et objectifs de technologies différentes

L’objectif est ainsi d’identifier, localiser et éventuellement suivre les drones en temps réel, en considérant différents environnements et conditions lumineuses.  

#### 1.1 Attentes du projet 
**Exigences de robustesse :**  
- Compatibilité avec toutes les technologies de caméras présentes dans le dataset.  
- Minimiser les faux négatifs (drones non détectés).  
- Capacité à expliquer les erreurs éventuelles autant que les réussites.  

**Aspects temps réel :**  
- Détection de drones en mouvement rapide (jusqu’à 100 km/h).  
- Même si le temps réel complet n’est pas atteignable dans le cadre du projet, la solution doit être conçue de manière à pouvoir être projetée vers du temps réel.  

**Informations attendues sur le drone :**  
- Coordonnées du drone par rapport à la caméra.  
- Orientation et direction du drone (prépondérante).  
- Distance au drone (utile pour l’évaluation du risque).  
- Possibilité de prédire la prochaine position du drone.  

**Critères de sécurité :**  
- Détection à une distance critique dépendant de la hauteur et de la vitesse du drone.  
- Évaluation de la dangerosité du drone : menace ou non pour l’environnement ou l’utilisateur.

### 2. Identification des verrous technologiques
- **Formats et tailles des vidéos :** les flux vidéo peuvent être dans des formats variés et certains fichiers peuvent être très volumineux.  
- **Précision de la détection :** le système doit détecter tous les drones sans générer trop de fausses alertes sur d’autres objets en mouvement.  
- **Portée de détection :** déterminer à quelle distance un drone peut être identifié avec fiabilité.
- **Temps réel :** traiter le flux vidéo en direct sans retard significatif.  
- **Variabilité des environnements :** gérer différents arrière-plans et éléments présents autour du drone pouvant compliquer la détection.

### 3. Description de la solution proposée long terme (si plus de temps)
 

### 4. Description du prototype qui sera réalisé (dans les heures de projet)
