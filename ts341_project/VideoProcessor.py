"""
VideoProcessor - Orchestrateur multiprocessus propre

Composition de tous les processus avec architecture statique pour éviter les problèmes de pickling.
"""

from multiprocessing import Queue, Event
from typing import Any, Optional, Union, Type
import cv2
import time
import logging

from ts341_project.VideoReader import VideoReader
from ts341_project.pipeline.PipelineProcessor import PipelineProcessor
from ts341_project.pipeline.ProcessingPipeline import ProcessingPipeline
from ts341_project.display import DisplayProcess
from ts341_project.storage import StorageProcess

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Orchestrateur multiprocessus pour pipeline vidéo.

    Architecture propre avec méthodes statiques pour éviter les problèmes
    de pickling (Queue/Event dans self).
    """

    def __init__(
        self,
        source: Any,
        pipeline: Union[str, ProcessingPipeline, Type[ProcessingPipeline]],
        enable_display: bool = True,
        enable_display_raw: bool = False,
        enable_storage: bool = False,
        output_path: str = "output.mp4",
        display_window: str = "Processing",
        display_raw_window: str = "Raw (Live)",
        max_display_height: int = 720,
        realtime: bool = False,
        codec: str = "mp4v",
        log_queue: Queue = None,
    ):
        """
        Args:
            source: Source vidéo (chemin, int webcam, etc.)
            pipeline: Pipeline de traitement (str, ProcessingPipeline instance, ou classe)
            enable_display: Activer affichage du traité
            enable_display_raw: Activer affichage de l'original (live)
            enable_storage: Activer sauvegarde
            output_path: Chemin de sortie
            display_window: Nom fenêtre du traité
            display_raw_window: Nom fenêtre de l'original
            max_display_height: Hauteur max affichage
            realtime: Mode temps réel (limiter FPS)
            codec: Codec vidéo (mp4v, MJPG, etc.)
        """
        self.source = source
        self.pipeline = pipeline
        self.enable_display = enable_display
        self.enable_display_raw = enable_display_raw
        self.enable_storage = enable_storage
        self.output_path = output_path
        self.display_window = display_window
        self.display_raw_window = display_raw_window
        self.max_display_height = max_display_height
        self.realtime = realtime
        self.codec = codec
        self.log_queue = log_queue

        # Events
        self.stop_event = Event()

        # Queues pour le processor (depuis reader)
        self.reader_queue = Queue(maxsize=10)

        # Queues pour les outputs du processor
        self.output_queues = {}

        if enable_display:
            self.output_queues["display"] = Queue(maxsize=10)

        if enable_storage:
            self.output_queues["storage"] = Queue(maxsize=10)

        # Queue dédiée pour l'affichage raw (directement depuis reader)
        self.raw_display_queue = None
        if enable_display_raw:
            self.raw_display_queue = Queue(maxsize=10)

        # Processus (initialisés dans start)
        self.processes = []

    def _detect_video_properties(self):
        """Détecte les propriétés vidéo pour le writer"""
        is_webcam = isinstance(self.source, int)

        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            raise RuntimeError(f"Impossible d'ouvrir la source: {self.source}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        if fps == 0 or is_webcam:
            fps = 30.0  # Default

        cap.release()

        return width, height, fps, is_webcam

    def start(self):
        """Démarre tous les processus"""
        logger.info("Initialisation...")

        # Détecter propriétés
        width, height, fps, is_webcam = self._detect_video_properties()

        logger.info(f"Source: {self.source}")
        logger.info(f"Résolution: {width}x{height} @ {fps} FPS")
        logger.info(
            f"Display Processed: {self.enable_display}, "
            f"Display Raw: {self.enable_display_raw}, Storage: {self.enable_storage}"
        )

        # 1. Créer les consommateurs d'abord

        # Display RAW (frames originales, direct depuis reader)
        if self.enable_display_raw:
            display_raw = DisplayProcess(
                display_queue=self.raw_display_queue,
                stop_event=self.stop_event,
                window_name=self.display_raw_window,
                max_height=self.max_display_height,
                log_queue=self.log_queue,
            )
            display_raw.start()
            self.processes.append(display_raw)
            logger.info("Display Raw démarré")

        # Display PROCESSED (frames traitées, depuis processor)
        if self.enable_display:
            display = DisplayProcess(
                display_queue=self.output_queues["display"],
                stop_event=self.stop_event,
                window_name=self.display_window,
                max_height=self.max_display_height,
                log_queue=self.log_queue,
            )
            display.start()
            self.processes.append(display)
            logger.info("Display Processed démarré")

        if self.enable_storage:
            storage = StorageProcess(
                storage_queue=self.output_queues["storage"],
                stop_event=self.stop_event,
                output_path=self.output_path,
                fps=fps,
                width=width,
                height=height,
                codec=self.codec,
                log_queue=self.log_queue,
            )
            storage.start()
            self.processes.append(storage)
            logger.info("Storage démarré")

        # 2. Créer le processor
        processor = PipelineProcessor(
            pipeline=self.pipeline,
            input_queue=self.reader_queue,
            output_queues=self.output_queues,
            stop_event=self.stop_event,
            log_queue=self.log_queue,
        )
        processor.start()
        self.processes.append(processor)
        logger.info("Processor démarré")

        # 3. Créer le reader (producteur) en dernier
        time.sleep(0.5)  # Laisser temps aux consommateurs
        reader = VideoReader(
            source=self.source,
            output_queue=self.reader_queue,
            stop_event=self.stop_event,
            realtime=self.realtime,
            raw_display_queue=self.raw_display_queue,
            log_queue=self.log_queue,
        )
        reader.start()
        self.processes.append(reader)
        logger.info("Reader démarré")

        logger.info("Tous les processus actifs ✓")
        return self

    def wait(self):
        """Attend la fin de tous les processus"""
        logger.info("En attente de fin...")
        try:
            for proc in self.processes:
                if hasattr(proc, "process"):
                    proc.process.join()
        except KeyboardInterrupt:
            logger.info("Interruption utilisateur")
            self.stop()

    def stop(self):
        """Arrête tous les processus"""
        logger.info("Arrêt demandé...")
        self.stop_event.set()

        # Arrêter dans l'ordre inverse
        for proc in reversed(self.processes):
            if hasattr(proc, "stop"):
                proc.stop()

        logger.info("Tous les processus arrêtés")

    def __enter__(self):
        """Support context manager"""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support context manager"""
        self.stop()
