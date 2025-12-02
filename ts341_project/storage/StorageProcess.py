"""
StorageProcess - Sauvegarde vidéo dans un processus dédié

Écrit les frames traitées dans un fichier vidéo
"""

from multiprocessing import Process, Queue, Event
import cv2
import time
import logging
from pathlib import Path
import subprocess
import shlex
import sys

logger = logging.getLogger(__name__)


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
        log_queue: Queue = None,
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
        self.log_queue = log_queue

        # Créer dossier de sortie
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _storage_process(
        storage_queue, stop_event, output_path, fps, width, height, codec, log_queue
    ):
        """Processus de sauvegarde"""
        # Configurer le logging pour ce processus
        if log_queue:
            from ts341_project.logging_config import MultiprocessLogging

            MultiprocessLogging.setup_child_process(log_queue)

        logger = logging.getLogger(__name__)
        logger.info(f"Démarrage - Sortie: {output_path}")

        # Préparer le writer. On essaie d'ouvrir directement le fichier demandé.
        out_path = Path(output_path)
        ext = out_path.suffix.lower()

        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height), True)

        # Si l'ouverture a échoué et que l'extension est .mp4, on bascule
        # vers un fichier temporaire .avi en MJPG puis on transcode avec ffmpeg
        use_transcode = False
        temp_avi = None
        if not writer.isOpened():
            logger.warning(
                f"VideoWriter unable to open {output_path} with codec '{codec}'"
            )
            # Fallback: write AVI with MJPG
            temp_avi = out_path.with_suffix(".avi")
            mjpg_fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            writer = cv2.VideoWriter(
                str(temp_avi), mjpg_fourcc, fps, (width, height), True
            )
            if not writer.isOpened():
                logger.error(f"Impossible d'ouvrir ni {output_path} ni {temp_avi}")
                return
            use_transcode = True

        frame_count = 0
        start_time = time.time()

        while not stop_event.is_set():
            try:
                data = storage_queue.get(timeout=0.5)

                # Fin de stream ?
                if isinstance(data, dict) and data.get("end_of_stream"):
                    logger.info("END_OF_STREAM reçu")
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
                    logger.info(f"{frame_count} frames | {fps_writing:.1f} FPS")

            except Exception:
                continue  # Queue vide

        writer.release()

        # Déterminer la source à vérifier / transcoder
        if use_transcode and temp_avi is not None:
            src_path = temp_avi
        else:
            src_path = out_path

        def probe_video_codec(path: Path) -> str:
            """Retourne le codec vidéo du premier stream via ffprobe, ou chaîne vide si échec."""
            try:
                cmd = [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=codec_name",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(path),
                ]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode != 0:
                    return ""
                return res.stdout.strip()
            except Exception:
                return ""

        written_codec = probe_video_codec(src_path)
        print(f"[NewStorageProcess] Codec détecté: '{written_codec}' pour {src_path}")

        # Si codec non-h264, essayer un transcodage pour produire un MP4 H.264 lisible
        try:
            needs_transcode = written_codec.lower() != "h264"
        except Exception:
            needs_transcode = True

        if needs_transcode:
            final_tmp = out_path.with_suffix(".tmp.mp4")
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(src_path),
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(final_tmp),
            ]
            print(
                f"[NewStorageProcess] Transcodage vers H.264: {' '.join(shlex.quote(a) for a in cmd)}"
            )
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                print(
                    f"[NewStorageProcess] ERREUR ffmpeg (returncode={res.returncode}): {res.stderr}"
                )
                print(f"[NewStorageProcess] ffmpeg stdout: {res.stdout}")
            else:
                try:
                    # Remplacer le fichier final par le transcodé
                    final_tmp.replace(out_path)
                    print(
                        f"[NewStorageProcess] Transcodage terminé et remplacé: {out_path}"
                    )
                    # Supprimer la source si c'était un .avi temporaire
                    if src_path != out_path and src_path.exists():
                        try:
                            src_path.unlink()
                        except Exception:
                            pass
                except Exception as e:
                    print(
                        f"[NewStorageProcess] Impossible de remplacer le fichier final: {e}"
                    )
        else:
            # Si on avait écrit dans un .avi temporaire et qu'il est déjà h264 (rare), déplacer
            if src_path != out_path and src_path.exists():
                try:
                    src_path.replace(out_path)
                    print(f"[NewStorageProcess] Déplacé {src_path} -> {out_path}")
                except Exception as e:
                    print(
                        f"[NewStorageProcess] Impossible de déplacer {src_path} -> {out_path}: {e}"
                    )

        elapsed = time.time() - start_time
        fps_avg = frame_count / elapsed if elapsed > 0 else 0

        logger.info(f"Arrêté - {frame_count} frames, {fps_avg:.1f} FPS")
        logger.info(f"Fichier: {output_path}")

    def start(self):
        """Démarre le processus"""
        self.process = Process(
            name="StorageProcess",
            target=StorageProcess._storage_process,
            args=(
                self.storage_queue,
                self.stop_event,
                self.output_path,
                self.fps,
                self.width,
                self.height,
                self.codec,
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
