#! /bin/bash

APP="seasonalnoisedMCMC_generic.py"

docker run -it \
    --name PiemonteTest \
    --mount type=bind,source=$(cd ..; pwd)/data,target=/home/jupuser/data \
    --env "PICKLEPREFIX"="2021-03-29_futbound_08_12" \
    --env "DATA_COL_NAME"="nuovi_positivi" \
    --env "PASTDAYS_START"="0" \
    --env "PASTDAYS_END"="0" \
    --env "FUTUREDRAWS"="10" \
    --env "TOT_CHAIN_LEN"="10" \
    --env "LOWER_RATIO"="0.8" \
    --env "UPPER_RATIO"="1.2" \
    --env "MC_TARGETACCEPT"="0.95" \
    --env "MC_TUNE"="5" \
    --env "MC_DRAWS"="20" \
    --env "MC_CORES"="1" \
    --env "REGION"="Piemonte"\
    covid-run-apps python3 $APP