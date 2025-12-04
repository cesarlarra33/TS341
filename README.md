# TS341 Project

**Équipe :**  
- ROBLIN Pauline  
- BASTIEN Hugo  
- ROUAULT Olivier  
- LARRAGUETA César 

Après avoir cloné le dépot git (branche main)

## Exécution avec Docker

Cette section explique comment construire et lancer l'application dans un conteneur Docker

Pré-requis:
- Docker Desktop installé et en cours d'exécution.

1) Construire l'image Docker (depuis la racine du projet):

```powershell
cd .\TS341
docker build -t ts341 .
```

2) Lancer un conteneur :

```powershell
docker run -p 8501:8501 -it ts341 /bin/bash

# Puis, à l'intérieur du conteneur, lancer l'application 
"(root@b5c5c50950eb:/app#)" poetry run streamlit run app.py
```

Cliquer sur le lien vers la page http (http://localhost:8501)

3) Sur l'interface steamlit :
- Selectionner une vidéo à traiter 
- (ignorer les blocs image et vidéo + ordre d'application pour lancer le pipeline de detection de drone) 
- Selectionner un Pipeline à utiliser : *drone-detection*
- Lancer le traitement (il peut prendre quelques minutes)
- Visualiser la vidéo traitée et les loggs générés après traitement

## Exécution de YOLO 
Pré-requis:
- Avoir la bibliothèque ultralytics installée sur la machine 
- Avoir ajouté une vidéo dans le dossier tests (nommée : video.mp4)

```powershell
cd .\TS341\tests
python .\yolo_algo.py
```