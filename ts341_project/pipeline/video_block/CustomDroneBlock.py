import cv2
import numpy as np
from pathlib import Path
import logging

from ts341_project.ProcessingResult import ProcessingResult
from ts341_project.pipeline.video_block.StatefulProcessingBlock import (
    StatefulProcessingBlock,
)
from ts341_project.pipeline.image_block.ResizeBlock import ResizeBlock
from ts341_project.pipeline.image_block.ThresholdBlock import ThresholdBlock

logger = logging.getLogger(__name__)
from ts341_project.pipeline.image_block.MorphologyBlock import MorphologyBlock
from ts341_project.pipeline.image_block.GrayscaleBlock import GrayscaleBlock
from ts341_project.pipeline.image_block.MetadataOverlayBlock import MetadataOverlayBlock
from ts341_project.pipeline.video_block.BackgroundSubtractorBlock import (
    BackgroundSubtractorBlock,
)
from ts341_project.pipeline.video_block.ContourMatchingBlock import ContourMatchingBlock


class CustomDroneBlock(StatefulProcessingBlock):
    """
    Block de détection de drone utilisant MOG2 pour la détection de mouvement
    et ORB pour le matching de patterns.

    Adapté de script_test1_pauline.py pour l'architecture de pipeline.
    """

    def __init__(
        self,
        pattern_dir: str = None,
        min_matches: int = 2,
        mog2_history: int = 300,
        mog2_var_threshold: int = 20,
        orb_n_features: int = 300,  # keypoints
        min_contour_size: int = 5,  # ignorer petits objets
        resize_width: int = 1280,  # Frame traitée forcée à largeur 1280
    ):
        """
        Args:
            pattern_dir: Chemin vers le dossier contenant les images de patterns du drone
            min_matches: Nombre minimum de matches ORB pour confirmer un drone
            mog2_history: Nombre de frames d'historique pour MOG2
            mog2_var_threshold: Seuil de variance pour MOG2
            orb_n_features: Nombre de features ORB à détecter
            min_contour_size: Taille minimale des contours à analyser
        """
        # IMPORTANT: désactiver le preprocessing par défaut; on définit notre pipeline
        # de prétraitement en sous-blocs (Resize, éventuellement Gray si nécessaire)
        preprocessing = [ResizeBlock(target_width=resize_width)]
        super().__init__(preprocessing=preprocessing, use_default_preprocessing=False)
        self.name = "CustomDroneBlock"

        # Paramètres
        self.min_matches = min_matches
        self.min_contour_size = min_contour_size
        self.resize_width = resize_width

        # Utiliser un BackgroundSubtractorBlock réutilisable (préprocessing: Resize)
        self.bg_block = BackgroundSubtractorBlock(
            history=mog2_history,
            var_threshold=mog2_var_threshold,
            detect_shadows=False,
            preprocessing=[ResizeBlock(target_width=resize_width)],
        )

        # Kernel pour opérations morphologiques
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

        # Bloc de matching/contours qui encapsule ORB + patterns
        self.contour_block = ContourMatchingBlock(
            pattern_dir=pattern_dir,
            min_matches=min_matches,
            orb_n_features=orb_n_features,
            min_contour_size=min_contour_size,
            roi_size=(128, 128),
        )

        # Bloc de post-traitement pour afficher les métadonnées
        self.metadata_overlay = MetadataOverlayBlock(font_scale=0.7, thickness=2)

    def _load_patterns(self, pattern_dir: str):
        """Charge les patterns de drone pour le matching ORB (lecture en gray, resize 128x128)"""
        pattern_path = Path(pattern_dir)
        if not pattern_path.exists():
            logger.warning(f"Dossier patterns introuvable: {pattern_dir}")
            return

        for file_path in pattern_path.glob("*"):
            if file_path.suffix.lower() not in [".jpg", ".png", ".jpeg"]:
                continue

            img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            img_small = cv2.resize(img, (128, 128))
            # pattern loading moved to ContourMatchingBlock
            pass

    def process_with_memory(
        self, frame: np.ndarray, result: ProcessingResult
    ) -> ProcessingResult:
        """
        Traite une frame avec détection de mouvement MOG2 et matching ORB.

        Args:
            frame: Frame à traiter (BGR ou grayscale)
            result: Résultat de traitement (contient les métadonnées)

        Returns:
            ProcessingResult avec les détections dessinées
        """
        # 1) Resize a été appliqué en preprocessing via StatefulProcessingBlock
        # `frame` ici est déjà redimensionné si ResizeBlock était dans preprocessing

        # Travailler sur une copie couleur pour annotation
        color_frame = frame.copy()

        if len(color_frame.shape) == 2:
            color_frame = cv2.cvtColor(color_frame, cv2.COLOR_GRAY2BGR)

        # 2) Soustraction de fond via BackgroundSubtractorBlock
        bg_result = self.bg_block.process(color_frame)
        fg_mask = bg_result.frame

        # 3) Nettoyage du masque: seuillage + morphologie (ouverture + fermeture)
        fg_mask = (
            ThresholdBlock(threshold=250, max_value=255, threshold_type="binary")
            .process(fg_mask)
            .frame
        )
        fg_mask = (
            MorphologyBlock(operation="opening", kernel_size=3, iterations=1)
            .process(fg_mask)
            .frame
        )
        fg_mask = (
            MorphologyBlock(operation="closing", kernel_size=3, iterations=1)
            .process(fg_mask)
            .frame
        )

        # Stocker le masque dans les metadata pour que le bloc de contours y accède
        result.metadata["fg_mask"] = fg_mask

        # Déléguer l'étape finale (contours + matching + annotation) au nouveau bloc
        result.frame = color_frame
        result = self.contour_block.process(result.frame, result)

        # 4) Post-traitement: afficher les métadonnées sur la frame
        result = self.metadata_overlay.process(result.frame, result)

        return result
