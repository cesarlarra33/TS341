"""
NewPipelineProcessor - Traitement pipeline dans un processus dédié

Consomme les frames, applique le pipeline, distribue aux consommateurs
"""

from multiprocessing import Process, Queue, Event
import time
from typing import Union, Type

from ts341_project.pipeline.ProcessingPipeline import ProcessingPipeline
from ts341_project.ProcessingStats import ProcessingStats


class PipelineProcessor:
    """
    Processeur de pipeline multiprocessus.
    Lit depuis input_queue, traite, envoie vers output_queues.
    """

    def __init__(
        self,
        pipeline: Union[
            str, ProcessingPipeline, Type[ProcessingPipeline]
        ],  # ProcessingPipeline, str (nom), ou classe de pipeline
        input_queue: Queue,
        output_queues: dict,  # {'display': Queue, 'storage': Queue}
        stop_event: Event,
    ):
        """
        Args:
            pipeline: ProcessingPipeline instance, str (nom de pipeline), ou classe
            input_queue: Queue d'entrée (frames brutes)
            output_queues: Dict de queues de sortie
            stop_event: Event d'arrêt
        """
        # Importer ici pour éviter les imports circulaires
        from ts341_project.pipeline.Pipelines import create_pipeline

        # Convertir en instance de ProcessingPipeline si nécessaire
        self.pipeline = create_pipeline(pipeline)
        self.input_queue = input_queue
        self.output_queues = output_queues
        self.stop_event = stop_event

    @staticmethod
    def _processor_process(pipeline, input_queue, output_queues, stop_event):
        """Processus de traitement"""
        print("[NewPipelineProcessor] Démarré")

        frame_count = 0
        start_time = time.time()

        # Initialiser les stats
        stats = ProcessingStats()

        while not stop_event.is_set():
            try:
                # Récupérer frame
                data = input_queue.get(timeout=0.5)

                # Fin de stream ?
                if isinstance(data, dict) and data.get("end_of_stream"):
                    print("[NewPipelineProcessor] END_OF_STREAM reçu")
                    # Propager aux consommateurs
                    for queue in output_queues.values():
                        if queue is not None:
                            try:
                                queue.put({"end_of_stream": True}, timeout=1.0)
                            except Exception:
                                pass
                    break

                # Traiter
                frame = data["frame"]
                frame_number = data["frame_number"]

                # Mesurer le temps de traitement
                process_start = time.time()
                result = pipeline.process(frame)
                process_time = time.time() - process_start

                # Enregistrer le temps de traitement
                stats.add_time(process_time)
                frame_count += 1

                # Distribuer
                output_data = {
                    "frame": result.frame,
                    "frame_number": frame_number,
                    "metadata": result.metadata,
                    "processing_time": process_time,
                }

                for queue in output_queues.values():
                    if queue is not None:
                        try:
                            queue.put_nowait(output_data)
                        except Exception:
                            pass  # Queue pleine

                # Stats intermédiaires
                if frame_count % 100 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    avg_process_time = stats.get_mean() * 1000  # en ms
                    print(
                        f"[NewPipelineProcessor] {frame_count} frames | "
                        f"{fps:.1f} FPS | Temps traitement: {avg_process_time:.2f} ms"
                    )

            except Exception:
                continue  # Queue vide, on continue

        # Afficher les stats finales
        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0
        print(f"[NewPipelineProcessor] Arrêté - {frame_count} frames, {fps:.1f} FPS")

        # Afficher le résumé des statistiques
        stats.print_summary("Statistiques de traitement du pipeline")

    def start(self):
        """Démarre le processus"""
        self.process = Process(
            target=PipelineProcessor._processor_process,
            args=(self.pipeline, self.input_queue, self.output_queues, self.stop_event),
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
