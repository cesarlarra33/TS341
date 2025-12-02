"""
VideoReader - Lecture vidéo dans un processus dédié

Lit depuis webcam ou fichier vidéo et distribue les frames via Queue
"""

import cv2
import time
import logging
from multiprocessing import Process, Queue, Event
from typing import Union

logger = logging.getLogger(__name__)


class VideoReader:
    """
    Lecteur vidéo multiprocessus.
    Lit en continu et envoie les frames dans une queue.
    """

    def __init__(
        self,
        source: Union[str, int],
        output_queue: Queue,
        stop_event: Event,
        realtime: bool = False,
        raw_display_queue: Queue = None,
        log_queue: Queue = None,
    ):
        """
        Args:
            source: Chemin vidéo ou ID webcam (0, 1, ...)
            output_queue: Queue principale pour le traitement
            stop_event: Event pour arrêter la lecture
            realtime: Si True, respecte le FPS de la source
            raw_display_queue: Queue optionnelle pour affichage raw (sans traitement)
        """
        self.source = source
        self.output_queue = output_queue
        self.stop_event = stop_event
        self.realtime = realtime
        self.raw_display_queue = raw_display_queue
        self.log_queue = log_queue
        self.is_webcam = isinstance(source, int)

        # Propriétés (remplies au démarrage)
        self.fps = 0
        self.width = 0
        self.height = 0
        self.total_frames = 0

    def _get_video_info(self, cap):
        """Récupère les infos de la vidéo"""
        self.fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    @staticmethod
    def _reader_process(
        source,
        output_queue,
        stop_event,
        realtime,
        is_webcam,
        raw_display_queue,
        log_queue,
    ):
        """Processus de lecture (fonction statique pour multiprocessing)"""
        # Configurer le logging pour ce processus
        if log_queue:
            from ts341_project.logging_config import MultiprocessLogging

            MultiprocessLogging.setup_child_process(log_queue)

        logger = logging.getLogger(__name__)
        logger.info(f"Démarrage lecture - Source: {source}")

        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            logger.error(f"Impossible d'ouvrir {source}")
            return

        # Config webcam
        if is_webcam:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_time = 1.0 / fps if realtime and fps > 0 else 0

        has_raw_display = raw_display_queue is not None
        logger.info(
            f"FPS: {fps:.1f}, Realtime: {realtime}, Raw Display: {has_raw_display}"
        )

        frame_count = 0
        last_time = time.time()

        while not stop_event.is_set():
            # Timing pour mode realtime
            if frame_time > 0:
                elapsed = time.time() - last_time
                if elapsed < frame_time:
                    time.sleep(frame_time - elapsed)
            last_time = time.time()

            # Lecture
            ret, frame = cap.read()
            if not ret:
                logger.info("Fin de vidéo")
                # Signal de fin aux deux queues
                output_queue.put({"end_of_stream": True})
                if has_raw_display:
                    raw_display_queue.put({"end_of_stream": True})
                break

            frame_count += 1

            data = {
                "frame": frame,
                "frame_number": frame_count,
                "timestamp": time.time(),
            }

            # Envoi vers queue de traitement (bloquant avec retries pour gérer la backpressure)
            def _try_put(q, item, retries=3, timeout=0.5):
                for _ in range(retries):
                    try:
                        q.put(item, timeout=timeout)
                        return True
                    except:
                        if stop_event.is_set():
                            return False
                        continue
                return False

            _try_put(output_queue, data)

            # Envoi vers queue raw display (si activée)
            if has_raw_display:
                # envoyer une copie pour éviter partage d'objet entre processus
                _try_put(raw_display_queue, data.copy())

        cap.release()
        logger.info(f"Arrêté - {frame_count} frames lues")

    def start(self):
        """Démarre le processus de lecture"""
        # D'abord récupérer les infos (dans le process parent)
        cap = cv2.VideoCapture(self.source)
        if cap.isOpened():
            self._get_video_info(cap)
            cap.release()
            logger.info(f"Infos: {self.width}x{self.height} @ {self.fps:.1f} FPS")
        else:
            logger.warning(f"Impossible de lire les infos de {self.source}")

        # Lancer le processus de lecture
        self.process = Process(
            name="VideoReader",
            target=VideoReader._reader_process,
            args=(
                self.source,
                self.output_queue,
                self.stop_event,
                self.realtime,
                self.is_webcam,
                self.raw_display_queue,
                self.log_queue,
            ),
        )
        self.process.start()
        return self

    def stop(self):
        """Arrête le processus"""
        self.stop_event.set()
        if hasattr(self, "process"):
            self.process.join(timeout=2.0)
            if self.process.is_alive():
                self.process.terminate()
