"""
NewDisplayProcess - Affichage dans un processus dédié

Affiche les frames traitées en temps réel
"""

from multiprocessing import Process, Queue, Event
import cv2
from ts341_project.logging_utils import get_logger


class NewDisplayProcess:
    """
    Affichage multiprocessus avec OpenCV.
    """

    def __init__(
        self,
        display_queue: Queue,
        stop_event: Event,
        window_name: str = "Video Processing",
        max_height: int = 1080,
    ):
        """
        Args:
            display_queue: Queue d'entrée pour les frames
            stop_event: Event d'arrêt
            window_name: Nom de la fenêtre
            max_height: Hauteur max (redimensionnement auto si plus grand)
        """
        self.display_queue = display_queue
        self.stop_event = stop_event
        self.window_name = window_name
        self.max_height = max_height

    @staticmethod
    def _display_process(display_queue, stop_event, window_name, max_height):
        """Processus d'affichage"""
        logger = get_logger(__name__)
        logger.info(f"Démarrage - Fenêtre: {window_name}")

        try:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        except Exception as e:
            logger.error(f"ERREUR fenêtre: {e}")
            return

        frame_count = 0

        while not stop_event.is_set():
            try:
                data = display_queue.get(timeout=0.5)

                # Fin de stream ?
                if isinstance(data, dict) and data.get("end_of_stream"):
                    logger.info("END_OF_STREAM reçu")
                    break

                # Afficher
                frame = data["frame"]

                # Redimensionner si nécessaire
                h, w = frame.shape[:2]
                if h > max_height:
                    scale = max_height / h
                    frame = cv2.resize(frame, (int(w * scale), max_height))

                cv2.imshow(window_name, frame)

                # ESC pour quitter
                key = cv2.waitKey(1)
                if key == 27:
                    logger.info("ESC pressé")
                    stop_event.set()
                    break

                frame_count += 1

                if frame_count % 100 == 0:
                    logger.debug(f"{frame_count} frames affichées")

            except:
                continue  # Queue vide

        cv2.destroyWindow(window_name)
        logger.info(f"Arrêté - {frame_count} frames affichées")

    def start(self):
        """Démarre le processus"""
        self.process = Process(
            target=NewDisplayProcess._display_process,
            args=(
                self.display_queue,
                self.stop_event,
                self.window_name,
                self.max_height,
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
