#! /bin/bash

source .env
cd .. || exit 1

echo "Move wip data to definitive"
cp -v data/computed/WIP/$PLACEHOLDER_DATE*Rt*.pickle data/computed/italy/


run_notebook(){
    docker-compose exec -u 0 -e REF_DATE=$PLACEHOLDER_DATE \
    tfjupyter jupyter nbconvert --to=notebook --inplace --ExecutePreprocessor.enabled=True $1
}

run_notebook notebooks/italy/Rt_regions_auto.ipynb
run_notebook notebooks/Rt_on_italian_national_data_auto.ipynb