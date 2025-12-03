"""
NewVideoProcessor - Orchestrateur multiprocessus propre.

Composition de tous les processus avec architecture statique
pour éviter les problèmes de pickling.
"""

import multiprocessing as mp
import time
from multiprocessing import Queue
from multiprocessing.synchronize import Event as MPEvent
from typing import Any, Type, Union

import cv2

from ts341_project.display import NewDisplayProcess
from ts341_project.pipeline.PipelineProcessor import PipelineProcessor
from ts341_project.pipeline.ProcessingPipeline import ProcessingPipeline
from ts341_project.storage import NewStorageProcess
from ts341_project.VideoReader import VideoReader


class VideoProcessor:
    """Orchestrateur multiprocessus pour pipeline vidéo.

    Architecture propre avec méthodes statiques pour éviter les
    problèmes de pickling (Queue/Event dans self).
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
    ):
        """
        Newvideoprocessor - Orchestrateur multiprocessus propre.

        Args:
            source: Source vidéo (chemin, int webcam, etc.)
            pipeline: Pipeline de traitement (str, ProcessingPipeline
            instance, ou classe)
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

        # Events
        self.stop_event: MPEvent = mp.get_context().Event()

        # Queues pour le processor (depuis reader)
        self.reader_queue: Queue[Any] = Queue(maxsize=10)

        # Queues pour les outputs du processor
        self.output_queues: dict[str, Queue[Any]] = {}

        if enable_display:
            self.output_queues["display"] = Queue(maxsize=10)

        if enable_storage:
            self.output_queues["storage"] = Queue(maxsize=10)

        # Queue dédiée pour l'affichage raw (directement depuis reader)
        self.raw_display_queue: Queue[Any] | None = None
        if enable_display_raw:
            self.raw_display_queue = Queue(maxsize=10)

        # Processus (initialisés dans start)
        self.processes: list[Any] = []

    def _detect_video_properties(self):
        """Détecte les propriétés vidéo pour le writer."""
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
        """Démarre tous les processus."""
        print("[NewVideoProcessor] Initialisation...")

        # Détecter propriétés
        width, height, fps, is_webcam = self._detect_video_properties()

        print(f"[NewVideoProcessor] Source: {self.source}")
        print(f"[NewVideoProcessor] Résolution: {width}x{height} @ {fps} FPS")
        print(
            f"[NewVideoProcessor] Display Processed: "
            f"{self.enable_display}, "
            f"Display Raw: {self.enable_display_raw}, "
            f"Storage: {self.enable_storage}"
        )

        # 1. Créer les consommateurs d'abord

        # Display RAW (frames originales, direct depuis reader)
        if self.enable_display_raw:
            display_raw = NewDisplayProcess(
                display_queue=self.raw_display_queue,
                stop_event=self.stop_event,
                window_name=self.display_raw_window,
                max_height=self.max_display_height,
            )
            display_raw.start()
            self.processes.append(display_raw)
            print("[NewVideoProcessor] Display Raw démarré")

        # Display PROCESSED (frames traitées, depuis processor)
        if self.enable_display:
            display = NewDisplayProcess(
                display_queue=self.output_queues["display"],
                stop_event=self.stop_event,
                window_name=self.display_window,
                max_height=self.max_display_height,
            )
            display.start()
            self.processes.append(display)
            print("[NewVideoProcessor] Display Processed démarré")

        if self.enable_storage:
            storage = NewStorageProcess(
                storage_queue=self.output_queues["storage"],
                stop_event=self.stop_event,
                output_path=self.output_path,
                fps=fps,
                width=width,
                height=height,
                codec=self.codec,
            )
            storage.start()
            self.processes.append(storage)
            print("[NewVideoProcessor] Storage démarré")

        # 2. Créer le processor
        processor = PipelineProcessor(
            pipeline=self.pipeline,
            input_queue=self.reader_queue,
            output_queues=self.output_queues,
            stop_event=self.stop_event,
        )
        processor.start()
        self.processes.append(processor)
        print("[NewVideoProcessor] Processor démarré")

        # 3. Créer le reader (producteur) en dernier
        time.sleep(0.5)  # Laisser temps aux consommateurs
        reader = VideoReader(
            source=self.source,
            output_queue=self.reader_queue,
            stop_event=self.stop_event,
            realtime=self.realtime,
            raw_display_queue=self.raw_display_queue,
        )
        reader.start()
        self.processes.append(reader)
        print("[NewVideoProcessor] Reader démarré")

        print("[NewVideoProcessor] Tous les processus actifs ✓")
        return self

    def wait(self):
        """Attend la fin de tous les processus."""
        print("[NewVideoProcessor] En attente de fin...")
        try:
            for proc in self.processes:
                if hasattr(proc, "process"):
                    proc.process.join()
        except KeyboardInterrupt:
            print("\n[NewVideoProcessor] Interruption utilisateur")
            self.stop()

    def stop(self):
        """Arrête tous les processus."""
        print("[NewVideoProcessor] Arrêt demandé...")
        self.stop_event.set()

        # Arrêter dans l'ordre inverse
        for proc in reversed(self.processes):
            if hasattr(proc, "stop"):
                proc.stop()

        print("[NewVideoProcessor] Tous les processus arrêtés")

    def __enter__(self):
        """Support context manager."""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support context manager."""
        self.stop()
