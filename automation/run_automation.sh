#! /bin/bash
docker build -f Dockerfile -t rt-automation-image .

docker run -it \
    --name RTAutomation \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /usr/bin/docker:/usr/bin/docker \
    --mount type=bind,source=$(pwd)/results,target=/RTAutomation/results \
    --mount type=bind,source=$(pwd)/configs,target=/RTAutomation/configs \
    --env PREFIX_DATE=2021-03-29 \
    --env CONFIG_FILE=config_dev.json \
    rt-automation-image