import streamlit as st
import tempfile
import os
import subprocess
import shutil
from pathlib import Path
import re

st.set_page_config(page_title="TS341 - Traitement vidéo multiprocessus", layout="wide")
st.title("TS341 - Traitement vidéo multiprocessus")


# Layout : colonne gauche (1/3) = paramètres, colonne droite (2/3) = upload + preview + résultat
col_param, col_main = st.columns([1, 2])

with col_param:
    st.header("Paramètres du pipeline")
    image_blocks = [
        "CannyEdgeBlock", "GrayscaleBlock", "ColorFilterBlock", "ColorScaleBlock", "ThresholdBlock", "HistogramEqualizationBlock", "GaussianBlurBlock", "ProcessingBlock", "MorphologyBlock"
    ]
    video_blocks = [
        "BackgroundSubtractorBlock", "MotionDetectionBlock", "StatefulProcessingBlock"
    ]
    selected_image_blocks = st.multiselect("Blocs image_block", image_blocks)
    selected_video_blocks = st.multiselect("Blocs video_block", video_blocks)
    block_order = st.text_input(
        "Ordre d'application (ex: CannyEdgeBlock,MotionDetectionBlock,GrayscaleBlock)",
        value=','.join(selected_image_blocks + selected_video_blocks)
    )
    custom_pipeline_name = st.text_input("Nom du pipeline custom (lettres, chiffres, _)", value="mon_pipeline")
    pipelines_py_path = os.path.join("ts341_project", "pipeline", "Pipelines.py")
    create_pipeline = st.button("Créer le pipeline custom", key="create_pipeline_btn")
    pipeline_to_run = st.text_input("Nom du pipeline à utiliser (doit exister dans Pipelines.py)", value=custom_pipeline_name)
    run_pipeline = st.button("Lancer le traitement vidéo", key="run_video_btn")

with col_main:
    # Découpage vertical de la colonne principale
    up_area, res_area = st.container(), st.container()
    with up_area:
        st.subheader("1. Upload d'une vidéo")
        uploaded_file = st.file_uploader("Choisissez une vidéo à traiter", type=["mp4", "avi", "mov"])
        video_path = None
        if uploaded_file:
            temp_dir = tempfile.mkdtemp()
            video_path = os.path.join(temp_dir, uploaded_file.name)
            with open(video_path, "wb") as f:
                f.write(uploaded_file.read())
            st.video(video_path)

    with res_area:
        st.subheader("2. Résultat du traitement")
        if 'processing' not in st.session_state:
            st.session_state['processing'] = False
        # Création pipeline custom si demandé
        if uploaded_file and create_pipeline:
            safe_name = re.sub(r'\W|^(?=\d)', '_', custom_pipeline_name)
            class_name = f"Custom{safe_name.capitalize()}Pipeline"
            block_names = [b.strip() for b in block_order.split(",") if b.strip()]
            block_imports = []
            block_inits = []
            for b in block_names:
                if b in image_blocks:
                    block_imports.append(f"from ts341_project.pipeline.image_block.{b} import {b}")
                    block_inits.append(f"            {b}(),")
                elif b in video_blocks:
                    block_imports.append(f"from ts341_project.pipeline.video_block.{b} import {b}")
                    block_inits.append(f"            {b}(),")
            block_imports = list(dict.fromkeys(block_imports))
            pipeline_code = f'''import sys\nfrom ts341_project.pipeline.ProcessingPipeline import ProcessingPipeline\n{chr(10).join(block_imports)}\n\nclass {class_name}(ProcessingPipeline):\n    def __init__(self):\n        super().__init__(blocks=[\n{chr(10).join(block_inits)}\n        ])\n        self.name = "{safe_name}"\n'''
            pipeline_file_path = os.path.join("ts341_project", "pipeline", f"custom_{safe_name}.py")
            with open(pipeline_file_path, "w") as f:
                f.write(pipeline_code)
            st.success(f"Pipeline custom créé : {pipeline_file_path}")
            # Ajout à Pipelines.py
            with open(pipelines_py_path, "r") as f:
                pipelines_py = f.read()
            import_line = f"from ts341_project.pipeline.custom_{safe_name} import {class_name}"
            if import_line not in pipelines_py:
                pipelines_py = import_line + "\n" + pipelines_py
            if f'"{safe_name}": {class_name}' not in pipelines_py:
                pipelines_py = pipelines_py.replace(
                    "AVAILABLE_PIPELINES = {",
                    f'AVAILABLE_PIPELINES = {{\n    "{safe_name}": {class_name},'
                )
            with open(pipelines_py_path, "w") as f:
                f.write(pipelines_py)
            st.info(f"Ajouté à Pipelines.py sous le nom : {safe_name}")
        # Lancer le pipeline si demandé
        if uploaded_file and run_pipeline:
            st.session_state['processing'] = True
            dest_video = os.path.join("ts341_project", "choosen_video" + Path(video_path).suffix)
            shutil.copy(video_path, dest_video)
            output_path = "ts341_project/output/output.mp4"
            cmd = [
                "poetry", "run", "python", "ts341_project/new_main.py",
                dest_video,
                "--pipeline", pipeline_to_run,
                "--save", output_path,
                "--no-display"
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
            st.session_state['processing'] = False
        elif not uploaded_file:
            st.info("Veuillez uploader une vidéo pour commencer.")
