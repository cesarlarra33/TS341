"""
Système de logging centralisé pour architecture multiprocessus.

Utilise un processus dédié qui collecte les logs de tous les autres processus
via une Queue partagée.
"""

import logging
import multiprocessing as mp
from multiprocessing import Queue
from logging.handlers import QueueHandler, QueueListener
import sys
from typing import Optional


class CustomFormatter(logging.Formatter):
    """Formatteur personnalisé pour nettoyer les noms de modules."""

    def format(self, record):
        # Enlever le préfixe ts341_project. des noms de modules
        if record.name.startswith("ts341_project."):
            record.name = record.name[14:]  # Longueur de 'ts341_project.'

        # Utiliser le nom du module au lieu du processName générique
        # Extraire juste le dernier segment du nom de module
        module_parts = record.name.split(".")
        if len(module_parts) > 0:
            record.processName = module_parts[-1]

        return super().format(record)


class MultiprocessLogManager:
    """
    Gestionnaire de logs pour environnement multiprocessus.

    Utilise une Queue pour centraliser les logs de tous les processus
    et un QueueListener pour les écrire de manière thread-safe.
    """

    def __init__(self, level: int = logging.INFO, log_file: Optional[str] = None):
        """
        Args:
            level: Niveau de log (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Chemin optionnel pour sauvegarder les logs dans un fichier
        """
        self.log_queue = mp.Manager().Queue(-1)
        self.level = level
        self.log_file = log_file
        self.listener = None

    def start(self):
        """Démarre le listener qui collecte les logs."""
        # Configuration des handlers
        handlers = []

        # Handler console avec formatteur personnalisé
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            CustomFormatter(
                "[%(processName)s] %(asctime)s - %(levelname)s - %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        handlers.append(console_handler)

        # Handler fichier (optionnel)
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(
                CustomFormatter(
                    "%(asctime)s - %(processName)s - %(levelname)s - %(message)s"
                )
            )
            handlers.append(file_handler)

        # Créer et démarrer le listener
        self.listener = QueueListener(
            self.log_queue, *handlers, respect_handler_level=True
        )
        self.listener.start()

    def stop(self):
        """Arrête le listener."""
        if self.listener:
            self.listener.stop()

    def get_logger(self, name: str) -> logging.Logger:
        """
        Crée un logger configuré pour envoyer vers la queue centrale.

        Args:
            name: Nom du logger (généralement __name__ du module)

        Returns:
            Logger configuré avec QueueHandler
        """
        logger = logging.getLogger(name)
        logger.setLevel(self.level)

        # Éviter les doublons si déjà configuré
        if not logger.handlers:
            queue_handler = QueueHandler(self.log_queue)
            logger.addHandler(queue_handler)

        return logger


# Instance globale pour faciliter l'usage
_global_log_manager: Optional[MultiprocessLogManager] = None


def setup_logging(
    level: int = logging.INFO, log_file: Optional[str] = None
) -> MultiprocessLogManager:
    """
    Configure le système de logging global pour le multiprocessing.

    À appeler UNE SEULE FOIS au démarrage de l'application principale.

    Args:
        level: Niveau de log
        log_file: Fichier de log optionnel

    Returns:
        Instance du MultiprocessLogManager
    """
    global _global_log_manager

    if _global_log_manager is not None:
        _global_log_manager.stop()

    _global_log_manager = MultiprocessLogManager(level=level, log_file=log_file)
    _global_log_manager.start()

    return _global_log_manager


def get_logger(name: str) -> logging.Logger:
    """
    Récupère un logger configuré pour le multiprocessing.

    Args:
        name: Nom du logger (utiliser __name__)

    Returns:
        Logger configuré

    Raises:
        RuntimeError: Si setup_logging() n'a pas été appelé
    """
    global _global_log_manager

    if _global_log_manager is None:
        raise RuntimeError(
            "Le système de logging n'est pas initialisé. "
            "Appelez setup_logging() au démarrage de l'application."
        )

    return _global_log_manager.get_logger(name)


def shutdown_logging():
    """Arrête le système de logging global."""
    global _global_log_manager

    if _global_log_manager is not None:
        _global_log_manager.stop()
        _global_log_manager = None
