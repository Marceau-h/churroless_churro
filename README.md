## Usage sur SACADO

- installer uv : https://docs.astral.sh/uv/getting-started/installation/
- cloner le repo dans le scratch
- uploader le build llama.cpp dans le scratch avec scp
- set `PATH="/scratch/username/llama.cpp/bin:$PATH"` dans le .env
- uploader les images
- configurer les variables d'env dans le fichier .env pour préciser l'endroit où sont le repo, le llama.cpp, les images, le dossier de sortie
- exemple de fichier de conf:

```env
PATH="/scratch/username/llama.cpp/bin:$PATH"

CHURROLESS_REPO_PATH="/scratch/username/churroless_churro"
CHURROLESS_OUTPUT_DIR="$CHURROLESS_REPO_PATH/outputs"
HF_HOME="$CHURROLESS_REPO_PATH/huggingface"

CHURROLESS_INPUT_DIR="$CHURROLESS_REPO_PATH/examples/mini_ballard"
CHURROLESS_IMAGE_FORMATS="jpg,png"
CHURROLESS_CONCURRENCY=20

CHURROLESS_KEY="dummy"
CHURROLESS_HOST_URL="http://127.0.0.1:8080"

CHURROLESS_MODEL="mradermacher/churro-3B-GGUF:Q8_0"
```
- lancer sbatch slurm_churroless_churro.bash
- récupérer les résultats dans $CHURROLESS_OUTPUT_DIR
