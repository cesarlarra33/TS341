"""Interface Streamlit pour le projet TS341.

Cette application permet de configurer un pipeline vidéo, uploader une vidéo
et lancer le traitement multiprocessus défini dans ts341_project.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import streamlit as st

from ts341_project.pipeline.Pipelines import list_pipelines

st.set_page_config(
    page_title="TS341 - Traitement vidéo multiprocessus", layout="wide"
)
st.title("TS341 - Traitement vidéo multiprocessus")


# Layout: colonne gauche (1/3)= paramètres, colonne droite (2/3)
# upload + preview + résultat
col_param, col_main = st.columns([1, 2])

with col_param:
    st.header("Paramètres du pipeline")
    image_blocks = [
        "CannyEdgeBlock",
        "GrayscaleBlock",
        "ColorFilterBlock",
        "ColorScaleBlock",
        "ThresholdBlock",
        "HistogramEqualizationBlock",
        "GaussianBlurBlock",
        "ProcessingBlock",
        "MorphologyBlock",
    ]
    video_blocks = [
        "BackgroundSubtractorBlock",
        "MotionDetectionBlock",
        "StatefulProcessingBlock",
        "CustomDroneBlock",
    ]
    selected_image_blocks = st.multiselect("Blocs image_block", image_blocks)
    selected_video_blocks = st.multiselect("Blocs video_block", video_blocks)
    block_order = st.text_input(
        "Ordre d'application (ex: MotionDetectionBlock,GrayscaleBlock)",
        value=",".join(selected_image_blocks + selected_video_blocks),
    )
    # Sélectionner un pipeline parmi ceux définis dans Pipelines.py
    available = list_pipelines()
    pipeline_names = [name for name, desc in available]
    pipeline_to_run = st.selectbox(
        "Pipeline à utiliser (défini dans Pipelines.py)", pipeline_names
    )
    run_pipeline = st.button("Lancer le traitement vidéo", key="run_video_btn")

with col_main:
    # Découpage vertical de la colonne principale
    up_area, res_area = st.container(), st.container()
    with up_area:
        st.subheader("1. Upload d'une vidéo")
        uploaded_file = st.file_uploader(
            "Choisissez une vidéo à traiter", type=["mp4", "avi", "mov"]
        )
        video_path: str | None = None
        if uploaded_file:
            temp_dir = tempfile.mkdtemp()
            video_path = os.path.join(temp_dir, uploaded_file.name)
            with open(video_path, "wb") as f:
                f.write(uploaded_file.read())
            st.video(video_path)

    with res_area:
        st.subheader("2. Résultat du traitement")
        if "processing" not in st.session_state:
            st.session_state["processing"] = False
        # NOTE: la création de pipelines custom a été désactivée.
        # Seuls les pipelines définis dans `Pipelines.py` peuvent
        # être sélectionnés via la selectbox.
        # Lancer le pipeline si demandé
        if uploaded_file and run_pipeline:
            assert video_path is not None
            st.session_state["processing"] = True
            dest_video = os.path.join(
                "ts341_project", "choosen_video" + Path(video_path).suffix
            )
            shutil.copy(video_path, dest_video)
            output_path = "ts341_project/output/output.mp4"
            cmd = [
                "poetry",
                "run",
                "python",
                "ts341_project/new_main.py",
                dest_video,
                "--pipeline",
                pipeline_to_run,
                "--save",
                output_path,
                "--no-display",
            ]
            st.write(f"Commande exécutée : {' '.join(cmd)}")
            with st.spinner("Traitement en cours..."):
                result = subprocess.run(cmd, capture_output=True, text=True)
                st.text(result.stdout)
                if result.returncode != 0:
                    st.error(f"Erreur : {result.stderr}")
                else:
                    if os.path.exists(output_path):
                        st.video(output_path)
                    else:
                        st.warning("Aucune vidéo de sortie trouvée.")
            st.session_state["processing"] = False
        elif not uploaded_file:
            st.info("Veuillez uploader une vidéo pour commencer.")
