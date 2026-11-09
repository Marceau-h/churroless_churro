## Usage sur HPC (SACADO ou autre)
Attention : L'ensemble des chemins sont pensés pour un usage sur SACADO, le dossier `/scratch/$USER` y est présent mais ce n'est peut-être pas le cas sur d'autres HPC. Il faudra donc adapter les chemins en conséquence.
Nous vous conseillons de créer un dossier `/scratch/$USER` sur le SACADO pour y mettre le repo, mais pas les images à traiter qui devraient optimalement être mises dans la partition store (/store/$USER).
Pour plus d'informations sur l'utilisation de SACADO, vous pouvez consulter la documentation officielle.
Aussi veillez à récupérer vos transcriptions car le dossier `/scratch/$USER` peut être nettoyé automatiquement.
### Installation
#### uv
````console
curl -LsSf https://astral.sh/uv/install.sh | sh
````

#### Cloner le repo
```console
cd /scratch/$USER
git clone https://github.com/Marceau-h/churroless_churro.git
```

#### Télécharger le build llama.cpp
```console
wget https://github.com/Marceau-h/llama_special_build/releases/download/v0.1.0/llama-tailored-static.tar.gz
mkdir /scratch/$USER/llama-tailored-static
tar -xzf llama-tailored-static.tar.gz -C /scratch/$USER/llama-tailored-static
rm -f llama-tailored-static.tar.gz
```

#### Uploader vos images
```console
rsync -avz /local/path/to/images/ $USER@sacado:/distant/path/to/images/
```

### Configuration
#### Variables d'environnement
Il y a un fichier d'exemple appelé `.env_example` dans le repo. Il faut le copier et le modifier pour qu'il corresponde à votre configuration. Et nommer la copie `.env`.

Les deux variables les plus à modifier sont :
- `CHURROLESS_INPUT_DIR` : le chemin vers le dossier contenant vos images à traiter (le chemin que vous avez mis à la place de `/distant/path/to/images/` dans la commande précédente)
- `CHURROLESS_IMAGE_FORMATS` : les formats d'images que vous voulez traiter, séparés par une virgule (`jpg,png` par défaut)

```console
cd /scratch/$USER/churroless_churro
cp .env_example .env
nano .env # modifier les variables d'environnement
```

### Utilisation
Pour lancer le traitement, il suffit d'aller dans le dossier du repo et de lancer le script `slurm_churroless_churro.bash` avec la commande `sbatch` :
```console
cd /scratch/$USER/churroless_churro
sbatch slurm_churroless_churro.bash
```

Les images seront traitées et les résultats seront sauvegardés dans le dossier `outputs` du repo si vous n'avez pas changé la variable `CHURROLESS_OUTPUT_DIR` dans le fichier `.env`.

Vous pouvez également surveiller l'avancement du traitement:
- vous pouvez voir tous vos jobs en cours avec la commande `squeue -u $USER` (ou `myqueue` sur SACADO), vous y verrez le nom, le temps d'exécution, l'état et l'ID du job. À noter que le temps d'exécution peut rester à 0 pendant un certain temps, l'état du job vous indiquera alors la raison de l'attente, veuillez alors consulter la documentation de SACADO ou de slurm pour plus d'informations.
- les logs du script sont dans le fichier `runs/churroless_churro_%j.out`, où `%j` est remplacé par l'ID du job que vous voyez dans la sortie de la commande `sbatch` ou dans la commande `squeue -u $USER. Vous pouvez donc consulter le fichier de log avec la commande ` cat runs/churroless_churro_<job_id>.out` ou `tail -f runs/churroless_churro_<job_id>.out` pour suivre l'avancement en temps réel.
- vous pouvez également regarder les transcriptions générées dans le dossier `outputs` du repo, elles seront nommées avec le nom de l'image d'origine et l'extension `.xml`.
- pour finir, les logs du serveur llama sont dans le fichier `runs/llama_server_%j.out`, où `%j` est remplacé par l'ID du job 

Si vous rencontrez des problèmes, veillez à joindre les fichiers de log du script et du serveur llama à votre demande d'aide (en faisant attention aux premieres lignes du log churroless_churro qui contiennent toutes les variables d'environnement et donc potentiellement des clés d'API, vous pouvez les supprimer avant de partager le log).
