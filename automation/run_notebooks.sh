#! /bin/bash

source .env

if [[ -z "${PLACEHOLDER_DATE}" ]]; then
    echo "Please set the PLACEHOLDER_DATE env variable!"
    exit 1
fi

cd .. || exit 1


run_notebook(){
    docker-compose exec -u 0 -e REF_DATE=$PLACEHOLDER_DATE \
    tfjupyter jupyter nbconvert --to=notebook --inplace --ExecutePreprocessor.enabled=True $1
}

run_notebook notebooks/Rt_on_italian_national_data.ipynb
run_notebook notebooks/italy/Rt_Piemonte.ipynb
run_notebook notebooks/italy/Rt_regions.ipynb
run_notebook notebooks/italy/Rt-all-regions.ipynb
run_notebook notebooks/italy/Rt_Sicilia.ipynb
run_notebook notebooks/italy/Rt_Valle_d_Aosta.ipynb
