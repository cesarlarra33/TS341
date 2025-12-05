import time
import numpy as np
from typing import List
from multiprocessing.pool import ThreadPool

from ts341_project.pipeline.image_block import ProcessingBlock
from ts341_project.ProcessingResult import ProcessingResult


class ProcessingPipeline:
    """
    Pipeline qui enchaîne plusieurs briques de traitement.
    Support du multi-threading pour paralléliser certains traitements.
    """

    def __init__(
        self,
        blocks: List[ProcessingBlock] = None,
        use_multicore: bool = False,
        num_workers: int = 4,
    ):
        """
        Args:
            blocks: Liste de briques de traitement à enchaîner
            use_multicore: Active le multi-threading (expérimental)
            num_workers: Nombre de workers pour le ThreadPool
        """
        self.blocks = blocks if blocks else []
        self.use_multicore = use_multicore
        self.num_workers = num_workers
        self.pool = None

        if self.use_multicore:
            self.pool = ThreadPool(processes=num_workers)

    def add_block(self, block: ProcessingBlock):
        """Ajoute une brique au pipeline"""
        self.blocks.append(block)
        return self

    def process(self, frame: np.ndarray) -> ProcessingResult:
        """
        Traite une frame à travers tout le pipeline.
        Args:
            frame: Image d'entrée
        Returns:
            ProcessingResult avec l'image traitée et les métadonnées
        """
        start_time = time.time()
        result = ProcessingResult(frame=frame)

        # Traitement séquentiel (les briques dépendent les unes des autres)
        for block in self.blocks:
            result = block.process(result.frame, result)

        result.processing_time = time.time() - start_time
        return result

    def __call__(self, frame: np.ndarray) -> ProcessingResult:
        return self.process(frame)

    def __del__(self):
        if hasattr(self, "pool") and self.pool:
            self.pool.close()
            self.pool.join()
