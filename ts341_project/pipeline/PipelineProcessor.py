"""
NewPipelineProcessor - Traitement pipeline dans un processus dédié

Consomme les frames, applique le pipeline, distribue aux consommateurs
"""

from multiprocessing import Process, Queue, Event
import time
from typing import Union, Type

from ts341_project.pipeline.ProcessingPipeline import ProcessingPipeline


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

        while not stop_event.is_set():
            try:
                # Récupérer frame
                data = input_queue.get(timeout=0.5)

                # Fin de stream ?
                if isinstance(data, dict) and data.get("end_of_stream"):
                    print("[NewPipelineProcessor] END_OF_STREAM reçu")
                    # Propager aux consommateurs
                    for name, queue in output_queues.items():
                        if queue is not None:
                            try:
                                queue.put({"end_of_stream": True}, timeout=1.0)
                            except:
                                pass
                    break

                # Traiter
                frame = data["frame"]
                frame_number = data["frame_number"]

                result = pipeline.process(frame)
                frame_count += 1

                # Distribuer
                output_data = {
                    "frame": result.frame,
                    "frame_number": frame_number,
                    "metadata": result.metadata,
                }

                for name, queue in output_queues.items():
                    if queue is not None:
                        try:
                            queue.put_nowait(output_data)
                        except:
                            pass  # Queue pleine

                # Stats
                if frame_count % 100 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    print(
                        f"[NewPipelineProcessor] {frame_count} frames | {fps:.1f} FPS"
                    )

            except:
                continue  # Queue vide, on continue

        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0
        print(f"[NewPipelineProcessor] Arrêté - {frame_count} frames, {fps:.1f} FPS")

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
