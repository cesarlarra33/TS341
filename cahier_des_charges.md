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

**3A - Spécialité Robotique et Apprentissage**

---
# I. Introduction

## I.1 Contexte du projet
L’utilisation des drones civils se développe rapidement, mais elle comporte des risques pour la sécurité et la vie privée. Il est donc crucial de pouvoir détecter et identifier les drones non autorisés sur certaines zones, à l'aide de différents types de caméras de surveillance. 

Dans ce contexte, une société spécialisée dans la protection de sites sensibles a sollicité le CATIE pour concevoir un système capable de repérer les drones à partir de flux vidéo provenant de différents types de caméras.

## I.2 Principaux objectifs
Le projet a pour objectif de concevoir un dispositif de détection de drones capable de fonctionner dans diverses situations :  
- À différentes altitudes  
- À plusieurs distances par rapport à la caméra  
- Sous des conditions d’éclairage variées  
- Avec des caméras et objectifs de technologies différentes  

L’objectif final est de **détecter, localiser et suivre** un modèle spécifique de drone en temps réel, tout en assurant la robustesse du système dans différents environnements.

---

# II. Exigences

## II.1 Exigences fonctionnelles
Le système devra remplir les fonctions suivantes :  

- **Entrée :** vidéo ou séquence d’images issues d’un dataset.  
- **Sortie :** coordonnées ou boîte englobante du drone, métriques de performance, visualisation des résultats.  
- **Traitement :** détection et suivi du drone.  
- **Compatibilité :** prise en charge de plusieurs technologies de caméras (dans un premier temps un seul modèle de drone, mais extensible à d’autres modèles).  

---

## II.2 Exigences de performance

| **Critère** | **Objectif** | **Remarques** |
|--------------|---------------|----------------|
| **Précision** | Minimiser les faux négatifs | Drones de tailles et formes variables selon le point de vue ; éviter les fausses détections. |
| **Vitesse** | Approche temps réel (objectif à long terme) | Le drone peut voler jusqu’à 100 km/h. |
| **Portabilité** | Exécution via Docker | Solution autonome et reproductible. |
| **Robustesse** | Résistance aux variations de caméra et de lumière | Validée sur un dataset diversifié. |
| **Lisibilité** | Sorties claires et interprétables | Logs, statistiques et visualisations compréhensibles. |

---

## II.3 Contraintes techniques

Le développement devra respecter les contraintes suivantes :  
- **Poetry :** gestion des dépendances et du packaging Python.  
- **Docker :** conteneurisation et portabilité.  
- **Logging :** mise en place d’un système de logs structuré.  
- **Typing :** annotations de type sur l’ensemble du code.  
- **PEP 8 :** respect des conventions de style Python.  

---

## II.4 Contraintes techniques recommandées

- **Tests unitaires :** utilisation de `pytest`.  
- **Documentation :** conforme à la norme **PEP 257**.  
- **Qualité du code :** linters `black`, `flake8`, `mypy`, `pylint`.  
- **Automatisation :** pre-commit hooks et intégration continue (CI/CD) via GitHub Actions.  

---

# III. Verrous technologiques et difficultés anticipées

## III.1 Liés aux données
- **Formats vidéo lourds et variés** : cela peut compliquer leur traitement et leur stockage.  
- **Différences entre les caméras** : certaines possèdent un objectif **fish-eye (185°)** tandis que d’autres ont un champ de vision plus restreint (**85,64°**).  
- Certaines vidéos ne disposent pas de **filtre infrarouge (IR)** : dominante de couleur rosée qui peut perturber les algorithmes de détection.  
- **Distance à partir de laquelle le drone devient visible**: peut fortement varier selon la résolution de la caméra et les conditions de prise.  

Cela nécessite donc de préparer minutieusement le dataset et de normaliser les sources avant de les placer en entrée de l'algorithme de détection. 
 

## III.2 Liés à la détection
- **Taille du drone qui peut être fortement réduite** : selon la distance dans la vidéo, la détection peut devenir plus complexe.  
- **Fonds d’image très variés et complexes** : les arbres, bâtiments, nuages, etc. augmentent considérablement le risque de fausses détections.  
- **Déplacement statiques ou très rapides du drone** : les grosses variations de vitesse peuvent compliquer la distinction entre le bruit environnant et mouvement réel.  
- **Risque de confusion avec d’autres objets en mouvement** : faux positifs tels que des oiseaux, des avions ou d'autres éléments du décor.  
- **Mouvements de caméra** : si la caméra est amenée à bouger elle-même, cela peut davantage compliquer le traitement des vidéos.

Cela nécessitent donc un modèle de détection robuste, précis et adaptable aux différents contextes de capture vidéo.

## III.3 Liés au traitement
- **Gérer des fichiers vidéo volumineux** : cela peut poser des problèmes de stockage et de performance.  
- **Contraintes de traitement en temps réel**: besoin d'une détection à l'instant t, qui nécessite un traitement rapide et peu coûteux en temps de calculs. 
- **Puissance de calcul disponible** : peut être limitée dans le cas d’une future embarcation, ce qui nécessite des algorithmes plus légers et optimisés.  

Cela nécessite donc une optimisation de l'algorithme de traitement afin d’assurer un fonctionnement stable et efficace, même dans des conditions matérielles restreintes.


# IV. Solution envisagée

---

## IV.1 Vision long terme (solution cible)

À long terme, la solution idéale viserait à développer un système complet de détection, d’identification et de suivi automatique des drones en temps réel, capable de fonctionner dans des environnements variés et avec différentes technologies.

Cette solution intègrerait :  
- Une **détection multi-capteurs**, combinant plusieurs types de caméras afin d’améliorer la robustesse face aux conditions lumineuses et météorologiques.  
- Un **modèle de détection basé sur l’intelligence artificielle**, entraîné sur un grand varié, représentant de nombreuses situations, afin d’obtenir la meilleure robustesse possible.  
- Une **localisation précise des coordonnées réelles du drone dans l’espace** (type GPS), en projetant les pixels des frames  dans le repère monde.  
- Une **intégration en temps réel**, avec une interface de visualisation affichant les positions des drones détectés à chaque instant, ainsi que l’ensemble des statistiques de détection pour aider à la prise de décision.  
- Un **système généralisable** à tout type de drone, incluant éventuellement une reconnaissance de charges dangereuses.  

L’objectif final serait de concevoir un système autonome, fiable et portable, utilisable pour la surveillance de tout type de zones.

## IV.2 Prototype à réaliser dans le cadre du projet

Dans le cadre du projet actuel, une version simplifiée du système sera développée afin de tester les algorithmes fondamentaux de la détection et du suivi d'objets en mouvement.  

Ce prototype comprendra :  
- Un **algorithme de traitement unique**, prenant en entrée une vidéo ou une séquence d’images issues du dataset fourni.  
- Une **interface en sortie** fournissant la position du drone sur chaque frame de la vidéo, les coordonnées détectées ainsi que des métriques de performance sur la qualité de la détection.  
- Une **reconnaissance basique des mouvements potentiellement dangereux**, tels que le rapprochement rapide ou une vitesse de déplacement anormalement élevée.
- Une **sortie décisionnelle** sous forme de **booléen**, indiquant si le drone détecté présente un risque potentiel ou non. 
- Une **infrastructure conteneurisée** (via **Docker**) garantissant la portabilité et la reproductibilité des tests.  
- Un **suivi de trajectoire** à l’aide de modèles simples de prédiction tels que **Kalman** (ou d’autres approches équivalentes).  
 

Ce prototype, permettra de valider la faisabilité technique du système et d’évaluer les performances des algorithmes choisis, en vue d’une intégration future sur des systèmes embarqués.

## IV.3 Stratégie prévisionnelle
1. **Prétraitement des images / vidéos**  
Les vidéos seront d’abord prétraitées afin de faciliter la détection du drone. Les techniques vues en cours seront appliquées comme par exemple :
     - **Ajustement de l’histogramme** et **égalisation** pour corriger les variations de luminosité.  
     - **Normalisation** des images.
     - **Suppression du fond** et des éléments statiques pour mettre en évidence le drone par rapport à l’environnement.  

2. **Détection par flux vidéo**  
Cette étape permettra de repérer le drone lorsqu'il est en mouvement, à l’aide d’algorithmes comme **MOG** ou d’autres méthodes de flux optique.   

3. **Extraction du drone parmi les pixels en mouvement**  
Une fois les zones mobiles détectées, un algorithme d’extraction sélectionnera les pixels correspondant spécifiquement au drone, en éliminant les faux positifs liés au bruit ou aux objets environnants. 

4. **Suivi et prédiction de trajectoire**  
Utilisation d’un **filtre de Kalman** (ou autre modèle prédictif simple) pour suivre la trajectoire du drone et prédire sa position future. Cela permettra d’anticiper les mouvements du drone et d’améliorer la précision du suivi et la détection de mouvements dangereux.  