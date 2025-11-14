# Structure du package ts341_project

## Organisation des modules

Architecture **multi-processus** modulaire pour le traitement vidéo en temps réel.

```
ts341_project/
├── __init__.py                 # Package principal
├── new_main.py                 # Point d'entrée CLI
├── VideoProcessor.py           # Orchestrateur multiprocessus
├── VideoReader.py              # Lecture vidéo dédiée
├── ProcessingResult.py         # Classe de résultat
├── ProcessingStats.py          # Statistiques de traitement
│
├── display/                    # Module d'affichage
│   ├── __init__.py            # Exports: DisplayProcess
│   └── DisplayProcess.py      # Affichage multiprocessus
│
├── storage/                    # Module de sauvegarde
│   ├── __init__.py            # Exports: StorageProcess
│   └── StorageProcess.py      # Sauvegarde multiprocessus
│
├── pipeline/                   # Module de pipeline
│   ├── __init__.py
│   ├── PipelineProcessor.py   # Traitement pipeline multiprocessus
│   └── ProcessingPipeline.py  # Classes de pipeline
│
└── movement_detection/         # Détection de mouvement
    ├── mog2.py
    ├── optical_flow.py
    └── README.md
```

## Utilisation

Afficher la vidéo de la webcam avec le pipeline "edge-enhance" :

```bash
python new_main.py 0 --pipeline edge-enhance
```

Traiter un fichier vidéo et sauvegarder le résultat :

```bash
python new_main.py video.mp4 --save output.mp4
```

---

Voir plus de fonctionnalités dans la documentation complète.

```bash
python new_main.py --help
```

---

## Ajout d'une pipeline personnalisée

```python
# dans new_main.py

class MyPipeline:
    def __init__(self):
        self.name = "My Pipeline"

    def process(self, frame):
        # Votre traitement ici
        processed = frame.copy()
        # ... modifications ...
        return ProcessingResult(processed)

```
