# Série d'alias pratique pour sacado
# Pour facilement les utiliser sur son compte on peut soit ajouter la ligne suivante à son .bashrc / .zshrc / .profile
# source [CHEMIN ABSOLU VERS CE FICHIER]
# (sans les crochets), i.e.
# source /home/$USER/churroless_churro/useful_aliasses

set -efau

GPU_PARTITION=gpu

alias gpu='srun -c 1 -G 1 -n 1 -N 1 -p ${GPU_PARTITION} --time=2:0:0 --pty /bin/bash'
alias wgpu="squeue -ap ${GPU_PARTITION} | grep --color=always -E '${USER}|$'"
alias wwgpu="watch -cx bash -c $'squeue -ap ${GPU_PARTITION} | grep --color=always -E \'${USER}|$\''"

set +efau