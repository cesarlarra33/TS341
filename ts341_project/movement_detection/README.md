# Codes d'exemples pour la détection de mouvement

**mog2.py** : Exemple d'utilisation de l'algorithme MOG2 pour la détection de mouvement dans une vidéo

**optical_flow.py** : Exemple d'utilisation de l'algorithme de flux optique pour la détection de mouvement dans une vidéo

##

Placer vos videos dans un dossier dédié `<directory>/` avant d'exécuter les scripts.
Puis modifiez les variables `directory` et `file` dans les scripts pour pointer vers votre vidéo.

Les vidéos traitées seront sauvegardées dans le dossier `<directory>/`.

Exemple :

    .
    ├── mog2.py
    ├── optical_flow.py
    ├── video_drone1
    │   ├── foreground_masks.avi
    │   ├── foreground_masks_double_threshold.avi
    │   ├── input_video.mp4
    │   ├── optical_flow.avi
    │   └── optical_flow_video_drone1.avi
    ├── video_drone2
    │   ├── foreground_masks_threshold128.avi
    │   ├── foreground_masks_threshold64.avi
    │   └── input_video.mp4
    └── video_drone3
        ├── foreground_masks_double_threshold_video_drone3.avi
        └── input_video.mp4
