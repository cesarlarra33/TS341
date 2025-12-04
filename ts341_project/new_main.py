#!/usr/bin/env python3
"""
new_main.py - Point d'entrée pour la nouvelle architecture multiprocessus

Usage:
    python new_main.py [source] [options]

Exemples:
    # Webcam avec affichage
    python new_main.py 0

    # Webcam avec affichage + sauvegarde
    python new_main.py 0 --save output.mp4

    # Fichier vidéo avec affichage
    python new_main.py video.mp4

    # Fichier vidéo avec sauvegarde uniquement (mode headless)
    python new_main.py video.mp4 --save output.mp4 --no-display

    # Webcam avec pipeline de traitement
    python new_main.py 0 --pipeline grayscale
"""

import sys
import argparse
from pathlib import Path
from typing import Union, Type

# Imports depuis le package ts341_project
from ts341_project.VideoProcessor import VideoProcessor
from ts341_project.pipeline import AVAILABLE_PIPELINES
from ts341_project.pipeline.ProcessingPipeline import ProcessingPipeline


# ============================================================================
# MAIN
# ============================================================================


def parse_args():
    """Parse les arguments en ligne de commande"""
    parser = argparse.ArgumentParser(
        description="Nouvelle architecture multiprocessus pour traitement vidéo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s 0                                    # Webcam avec affichage
  %(prog)s 0 --save output.mp4                  # Webcam avec affichage + sauvegarde
  %(prog)s video.mp4                            # Fichier avec affichage
  %(prog)s video.mp4 --save out.mp4 --no-display  # Headless (sauvegarde uniquement)
  %(prog)s 0 --pipeline dual                    # Webcam avec affichage dual
  %(prog)s 0 --pipeline edges                   # Webcam avec détection contours
        """,
    )

    parser.add_argument(
        "source",
        help="Source vidéo: 0 pour webcam, ou chemin vers fichier vidéo",
    )

    parser.add_argument(
        "--save",
        "-s",
        metavar="OUTPUT",
        help="Sauvegarder dans un fichier vidéo",
    )

    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Désactiver l'affichage (mode headless)",
    )

    parser.add_argument(
        "--display-raw",
        action="store_true",
        help="Afficher également les frames originales (avant traitement)",
    )

    parser.add_argument(
        "--pipeline",
        "-p",
        default="passthrough",
        choices=list(AVAILABLE_PIPELINES.keys()),
        help="Pipeline de traitement (défaut: passthrough)",
    )

    parser.add_argument(
        "--realtime",
        "-r",
        action="store_true",
        help="Mode temps réel (limiter FPS pour webcam)",
    )

    parser.add_argument(
        "--codec",
        "-c",
        default="mp4v",
        help="Codec vidéo pour sauvegarde (défaut: avc1 — H.264 compatible navigateurs)",
    )

    parser.add_argument(
        "--window",
        "-w",
        default="Video Processing",
        help="Nom de la fenêtre d'affichage",
    )

    parser.add_argument(
        "--max-height",
        "-m",
        type=int,
        default=720,
        help="Hauteur max d'affichage (défaut: 720)",
    )

    return parser.parse_args()


def main():
    """Point d'entrée principal"""
    args = parse_args()

    # Déterminer la source
    try:
        source = int(args.source)
        source_type = "Webcam"
    except ValueError:
        source = args.source
        source_type = "Fichier"
        if not Path(source).exists():
            print(f"Fichier introuvable: {source}")
            sys.exit(1)

    # Créer le pipeline (str sera converti en ProcessingPipeline par VideoProcessor)
    pipeline: Union[str, ProcessingPipeline, Type[ProcessingPipeline]] = args.pipeline

    # Configuration
    enable_display = not args.no_display
    enable_display_raw = args.display_raw
    enable_storage = args.save is not None
    
    if args.save:
        output_path = str(Path(args.save).with_suffix(".mp4"))
    else:
        output_path = "output.mp4"

    # Afficher la configuration
    print("=" * 60)
    print("Nouvelle Architecture Multiprocessus")
    print("=" * 60)
    print(f"Source:     {source_type} ({source})")
    print(f"Pipeline:   {args.pipeline}")
    print(f"Display Processed: {'ok' if enable_display else 'no'}")
    if enable_display_raw:
        print(f"Display Raw:       ✓ (Original avant traitement)")
    print(f"Storage:    {'ok' if enable_storage else 'no'}")
    if enable_storage:
        print(f"  Fichier:  {output_path}")
        print(f"  Codec:    {args.codec}")
    print(f"Realtime:   {'ok' if args.realtime else 'no'}")
    if enable_display or enable_display_raw:
        if enable_display:
            print(f"Window Processed: {args.window}")
        if enable_display_raw:
            print(f"Window Raw:       Raw (Live)")
        print(f"Max Height:       {args.max_height}")
    print("=" * 60)
    print()

    if enable_display:
        print("Appuyez sur ESC dans la fenêtre ou CTRL+C pour arrêter")
    else:
        print("Appuyez sur CTRL+C pour arrêter")
    print()

    # Lancer le traitement
    try:
        with VideoProcessor(
            source=source,
            pipeline=pipeline,
            enable_display=enable_display,
            enable_display_raw=enable_display_raw,
            enable_storage=enable_storage,
            output_path=output_path,
            display_window=args.window,
            max_display_height=args.max_height,
            realtime=args.realtime,
            codec=args.codec,
        ) as processor:
            processor.wait()

    except KeyboardInterrupt:
        print("\nInterruption utilisateur (CTRL+C)")

    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    print()
    print("=" * 60)
    print("Traitement terminé")
    if enable_storage:
        print(f"Fichier sauvegardé: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()