"""
Configuration du logging centralisé pour architecture multiprocessus

Utilise QueueHandler/QueueListener pour centraliser les logs de tous les processus
"""

import logging
import logging.handlers
from multiprocessing import Queue
from typing import Optional


class CenteredFormatter(logging.Formatter):
    """Formatter avec centrage personnalisé pour processName et levelname"""

    def format(self, record):
        # Centrer processName sur 20 caractères
        record.processName = record.processName.center(20)
        # Centrer levelname sur 8 caractères
        record.levelname = record.levelname.center(8)
        return super().format(record)


class MultiprocessLogging:
    """
    Gestionnaire de logging centralisé pour multiprocessing.

    Tous les processus envoient leurs logs via une Queue vers un QueueListener
    qui les traite dans le processus principal.
    """

    def __init__(self, log_level: int = logging.INFO):
        """
        Args:
            log_level: Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_level = log_level
        self.log_queue: Optional[Queue] = None
        self.queue_listener: Optional[logging.handlers.QueueListener] = None

    def setup_main_process(self) -> Queue:
        """
        Configure le logging dans le processus principal.

        Returns:
            Queue pour que les processus enfants envoient leurs logs
        """
        # Créer la queue de logs
        self.log_queue = Queue()

        # Créer le handler pour le processus principal
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)

        # Format des logs
        formatter = CenteredFormatter(
            "%(asctime)s [%(processName)s] [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )
        console_handler.setFormatter(formatter)

        # Créer le QueueListener qui écoute la queue et écrit les logs
        self.queue_listener = logging.handlers.QueueListener(
            self.log_queue, console_handler, respect_handler_level=True
        )

        # Démarrer le listener
        self.queue_listener.start()

        # Configurer le logger root du processus principal
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        root_logger.addHandler(console_handler)

        return self.log_queue

    def stop(self):
        """Arrête le QueueListener"""
        if self.queue_listener:
            self.queue_listener.stop()

    @staticmethod
    def setup_child_process(log_queue: Queue, log_level: int = logging.INFO):
        """
        Configure le logging dans un processus enfant.

        Args:
            log_queue: Queue vers laquelle envoyer les logs
            log_level: Niveau de logging
        """
        # Créer un QueueHandler pour ce processus
        queue_handler = logging.handlers.QueueHandler(log_queue)
        queue_handler.setLevel(log_level)

        # Configurer le logger root de ce processus
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Supprimer les handlers existants et ajouter le QueueHandler
        root_logger.handlers.clear()
        root_logger.addHandler(queue_handler)


def setup_logging(log_level: int = logging.INFO) -> MultiprocessLogging:
    """
    Configure le système de logging centralisé.

    Args:
        log_level: Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Instance de MultiprocessLogging configurée
    """
    mp_logging = MultiprocessLogging(log_level)
    mp_logging.setup_main_process()
    return mp_logging
