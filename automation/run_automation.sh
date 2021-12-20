#! /bin/bash
docker build --build-arg EXTERNALUSERID=$UID -f ../Dockerfile-app -t covid-run-apps ../
docker build -f app/Dockerfile -t rt-automation-image ./app || exit 1

echo "###################################"
echo "Running calculations with user id: "
docker run -it --rm covid-run-apps id -u jupuser
echo "###################################"

GOOD=true
source .env

if [[ -z "${PLACEHOLDER_DATE}" ]]; then
    echo "Please set the PLACEHOLDER_DATE env variable!"
    GOOD=false
fi

if [[ -z "${PLACEHOLDER_PROJECT_DIR}" ]]; then
    echo "Please set the PLACEHOLDER_PROJECT_DIR env variable!"
    GOOD=false
fi


if [[ -z "${CONFIG_FILE}" ]]; then
    echo "Please set the CONFIG_FILE env variable!"
    GOOD=false
fi

$GOOD || exit 1

docker run -it -d \
    --name RTAutomation \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /usr/bin/docker:/usr/bin/docker \
    --mount type=bind,source=$(pwd)/results,target=/RTAutomation/results \
    --mount type=bind,source=$(pwd)/configs,target=/RTAutomation/configs \
    --env PLACEHOLDER_DATE=$PLACEHOLDER_DATE \
    --env PLACEHOLDER_PROJECT_DIR=$PLACEHOLDER_PROJECT_DIR \
    --env CONFIG_FILE=$CONFIG_FILE \
    rt-automation-image
