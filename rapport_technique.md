# I. Solution mise en œuvre

L’application développée est fournie sous forme d’une image Docker. Cela permet d’avoir tout l’environnement déjà prêt : Python, les dépendances et les outils nécessaires. L’image utilise Poetry pour gérer les librairies Python, ce qui garantit que tout fonctionne de la même façon sur n’importe quel ordinateur.
Quand l’application est lancée, elle ouvre automatiquement une interface web Streamlit sur le navigateur, en local. Cette interface permet à l’utilisateur de :
- choisir la vidéo qu’il veut analyser,
- sélectionner le type de traitement à appliquer (pipeline),
- lancer le traitement,
- voir la vidéo d’origine et la vidéo traitée,
- consulter les performances obtenues (vitesse, précision, etc.).


## II. Méthodologie

### II.1 Architecture multi-cœur

Pour la structure du projet, nous avons opté pour une architecture **modulaire et multiprocessus**. Nous avons choisi cette organisation pour anticiper des usages en **quasi temps réel** et pour faciliter la maintenance des différents modules. Chaque étape du traitement (lecture, transformation, affichage et sauvegarde des images) s’exécute dans un processus indépendant. Ces processus communiquent via des *queues*, ce qui maximise le parallélisme et garantit une bonne réactivité, même sur des vidéos longues que nous avions dans le dataset.
- **VideoReader** lit les frames et les transmet dans une queue.  
- **PipelineProcessor** récupère chaque frame, applique le pipeline choisi et envoie le résultat.  
- **DisplayProcess** affiche en temps réel les frames annotées (désactivé en mode Docker).  
- **StorageProcess** enregistre la vidéo traitée et les éventuels fichiers de logs.
---

### II.2 Pipeline modulaire

Le projet repose également sur une architecture en pipeline, composée d’une succession de blocs spécialisés. Nous avons choisi de procéder de cette manière car la détection repose sur une succession de traitements qui peuvent être modulés de différentes façons lors des tests.
Deux types de blocs sont mis en place :

- **Image blocks** : opérations ne dépendant que de l’image actuelle 
- **Video blocks** : opérations nécessitant de la mémoire et une connaissance du contexte.

Les pipelines combinent ces blocs dans un ordre configurable, ce qui permet de tester facilement les combinaisons d'algorithmes sans modifier le code.
- Chaque pipeline hérite de `ProcessingPipeline` et expose une liste de blocs appliqués séquentiellement sur chaque frame. 
- Chaque image traitée donne ensuite un `ProcessingResult` qui contient l’image annotée et les informations utiles récupérées suite au traitement. 
- Le `StorageProcess` permet enfin de sauvegarder la vidéo complète formée des frames traitées, et peut également sauvegarder des fichiers de logs. 

---

### II.3 Interface

L’interface utilisateur est développée avec **Streamlit**, que nous avons choisi pour sa rapidité de mise en œuvre et sa simplicité d’intégration. Après exécution, la vidéo annotée ainsi que les logs du traitement sont affichés.

---

### II.4 Algorithme de détection implémenté dans Docker
L’algorithme implémenté dans Docker repose sur les méthodes classiques de traitement d’images. Le fonctionnement global repose sur une détection des zones en mouvement, puis d’une identification parmi elles des régions ressemblant à un drone :

1. *Redimensionnement de l’image (ResizeBlock)*: permet d’avoir une taille fixe de toutes les frames pour généraliser les seuils de détections et rendre le traitement plus stable d’une vidéo à l’autre, et réduire les frames trop grandes pour la rapidité du traitement 
2. *Soustraction de fond MOG2 (BackgroundSubstractorBlock)* :  permet de détecter les zones en mouvement, car nous sommes partis du principe que le drone est ajoritairement en mouvement dans les vidéos.
3. *Nettoyage du mask MOG2 (ThresholdBlock & MorphologyBlock)*: Seuillage sur les pixels, opérations morphologiques (opening et closing) pour supprimer au maximum le bruit et remplir les trous, afin d'éviter les faux positifs.
4. *Détection de régions par contours (ContourMatchingBlock)*: permet de sélectionner les zones assez grandes et ignorer les toutes petites zones en mouvement, en passant par des boîtes englobantes.
5. *Vérification par matching ORB (ORBMatchingBlock)* : sur chaque boîte, on compare les descripteurs ORB de la ROI avec les patterns de drones, afin de ne selectionner que les détections ressemblant à un drone et supprimer les mouvements parasites.
6. *Annotations* : dessin du rectangle autour du drone, affichage des coordonnées dans l’image, et métadonnées pour afficher la performance et faire le feedback à l'utilisateur. 

### II.5 Tests d'implémentation de YOLO
Avec les méthodes classiques de traitement d’image, nous avons vite atteint des limites, surtout dans les vidéos avec des arbres ou des arrière-plans complexes. Le système devait choisir entre rater le drone (faux négatifs) ou détecter trop de bruit (faux positifs). Pour améliorer cette situation, nous avons essayé une approche basée sur l’IA en entraînant un modèle YOLO.

