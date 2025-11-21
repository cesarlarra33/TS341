"""
StorageProcess - Sauvegarde vidéo dans un processus dédié

Écrit les frames traitées dans un fichier vidéo
"""

from multiprocessing import Process, Queue, Event
import cv2
import time
from pathlib import Path


class StorageProcess:
    """
    Sauvegarde vidéo multiprocessus.
    """

    def __init__(
        self,
        storage_queue: Queue,
        stop_event: Event,
        output_path: str,
        fps: float,
        width: int,
        height: int,
        codec: str = "mp4v",
    ):
        """
        Args:
            storage_queue: Queue d'entrée pour les frames
            stop_event: Event d'arrêt
            output_path: Chemin de sortie
            fps: FPS de sortie
            width: Largeur
            height: Hauteur
            codec: Codec fourcc (mp4v, MJPG, etc.)
        """
        self.storage_queue = storage_queue
        self.stop_event = stop_event
        self.output_path = output_path
        self.fps = fps
        self.width = width
        self.height = height
        self.codec = codec

        # Créer dossier de sortie
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _storage_process(
        storage_queue, stop_event, output_path, fps, width, height, codec
    ):
        """Processus de sauvegarde"""
        print(f"[StorageProcess] Démarrage - Sortie: {output_path}")

        # Créer le writer
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height), True)

        if not writer.isOpened():
            print(f"[StorageProcess] ERREUR: Impossible d'ouvrir {output_path}")
            return

        frame_count = 0
        start_time = time.time()

        while not stop_event.is_set():
            try:
                data = storage_queue.get(timeout=0.5)

                # Fin de stream ?
                if isinstance(data, dict) and data.get("end_of_stream"):
                    print("[StorageProcess] END_OF_STREAM reçu")
                    break

                # Écrire
                frame = data["frame"]

                # Adapter dimensions
                h, w = frame.shape[:2]
                if (h, w) != (height, width):
                    frame = cv2.resize(frame, (width, height))

                # Adapter couleur
                if len(frame.shape) == 2:
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                elif len(frame.shape) == 3 and frame.shape[2] == 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                writer.write(frame)
                frame_count += 1

                if frame_count % 100 == 0:
                    elapsed = time.time() - start_time
                    fps_writing = frame_count / elapsed
                    print(
                        f"[StorageProcess] {frame_count} frames | {fps_writing:.1f} FPS"
                    )

            except:
                continue  # Queue vide

        writer.release()

        elapsed = time.time() - start_time
        fps_avg = frame_count / elapsed if elapsed > 0 else 0

        print(f"[StorageProcess] Arrêté - {frame_count} frames, {fps_avg:.1f} FPS")
        print(f"[StorageProcess] Fichier: {output_path}")

    def start(self):
        """Démarre le processus"""
        self.process = Process(
            target=StorageProcess._storage_process,
            args=(
                self.storage_queue,
                self.stop_event,
                self.output_path,
                self.fps,
                self.width,
                self.height,
                self.codec,
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
