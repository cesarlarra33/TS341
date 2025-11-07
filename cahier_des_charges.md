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


