# Short version

How to run the calculation of the $Rt$ index at national italian level and for each region.

## Prerequisites

1. have docker installed on your machine
2. clone this repo: `git clone git@github.com:tomorrowdata/COVID-19.git`
3. create the the directory `WIP` inside the path `COVID-19/data/computed/`
4. create a file named `.env` in the directory `COVID-19/automation` with the following content:
```
CONFIG_FILE="config.json"
PLACEHOLDER_PROJECT_DIR=$(cd ..; pwd)
# the following date should be changed at each run
PLACEHOLDER_DATE="2021-12-05"
```

## Steps to be repeated for each run

### Start the calculation:
1. go to `COVID-19`
2. run `git pull` 
    - a series of files available from your last run will be pulled
3. run `docker rm $(docker ps -aq)` 
    - to remove containers created from previous calculations
4. eventually remove all the files resulted from previous calculations, which are contained in the path 
5. go to `COVID-19/automation`
6. edit the file `.env` changing the `PLACEHOLDER_DATE` to the last day for which DPC (Protezione Civile) data is available.
    - For example: if it is monday morning 2021-12-06, you must set 2021-12-05, which is the the last day for which new data are available
`COVID-19/data/computed/WIP`
7. finally, from the same path `COVID-19/automation`, 
    - run the command: `./run_automation.sh`
8. the command will calculate the $Rt$ for Italy and for each region, processing 4 regions in parallel, one container for each region

### Check the status

... The entire calculation require some hours, depending on the machine ... 

In the meanwhile you can check what is happening whith the following:
- `docker ps`: lists the regions which are currently under calculation
    - if no container is running, either the computation is completed, or something went wrong
- `docker logs Italy` (or the name of a region): shows the logs of the calculation

### Commit the results

> **Note**: the following steps require that you have ush access to the original repo (either this one or a fork)

When the processing is done, to commit and push the results:
1. go to `COVID-19/automation`
2. run `./run_push_wip.sh`
3. This will perform two main actions:
    1. update all the relevant notebooks with the results of the calculations
    2. push all the notebooks, pickle files and images on a new branch named `WIP_<the date in $PLACEHOLDER_DATE>`
        - you will be required for your github personal access token for the push to be successful




# Run Automation
Use the `run_automation.sh`  Automation App to run different application as defined in `./configs/config.json`.

**Features**
- Define applications to be run using a *JSON* config file
- Set a maximum number of parallel runs
- Provide reports for each run, including docker container logs


##  Run the automation
In order to start the automation, some env variables has to be set:
- `PLACEHOLDER_DATE`: replaces the *DATE* placeholder in the JSON config file
- `PLACEHOLDER_PROJECT_DIR`: replaces the *PROJECT_DIR* placeholder in the JSON config file
- `CONFIG_FILE`: the name of the config file to be used (saved in */configs*)


> It is possible to defined a `.env` file with those variables which will be sourced in the provided script.


Then launch the Automation App to schedule the runs defined in the configuration file.

<hr>

## Automation Config File
The json config file is organized as follow:

```json
{
    "runs": [],
    "max_parallel_containers" : 4,
    "run_results_dir": "./results"
}
```
- `max_parallel_containers`: how many runs in parallel
- `run_results_dir`: dir where to save run results
- `runs`: list of json objects defining each single runs

### Define a run
In order to define a run, the following JSON structure is used.

An example for running *seasonalnoisedMCMC_generic* python application for computing Italy's Rt:

```json
{
    "name": "Italy",
    "image": "covid-run-apps",
    "data": {
        "source": "{PROJECT_DIR}/data/",
        "target": "/home/jupuser/data"
    },
    "app": "seasonalnoisedMCMC_generic",
    "args": {
        "PICKLEPREFIX": "{DATE}_futbound_08_12",
        "DATA_COL_NAME": "nuovi_positivi",
        "PASTDAYS_START": 0,
        "PASTDAYS_END": 0,
        "FUTUREDRAWS": 10,
        "TOT_CHAIN_LEN": null,
        "LOWER_RATIO": 0.8,
        "UPPER_RATIO": 1.2,
        "MC_TARGETACCEPT": 0.95,
        "MC_TUNE": 500,
        "MC_DRAWS": 1000,
        "MC_CORES": 4,
        "REGION": null
    }
}
```
When `args.REGION` is set to *null*, national data is used for computing the Rt from the provided dataframe.

- `name`: the name used for the run and for the docker container
- `image`: the docker-image used for running the container
- `app`: python application to execute inside the container
- `data`: used for biding the volume containing data for the application
- `args`: arguments for the python application

**NOTE 1**: the placeholders `PROJECT_DIR` and `DATE` will be replaced dynamically based on specific env variables which has to be defined before launching the script.

**NOTE 2**: the specified image should have been built previously otherwise the Automation App will raise an error.


## Results
Results are stored in `./results`.
Each times the `./run_automation.sh` script is executed and at least one run is terminated, a new directory is created in order to store each single run result.

The report is named with the following convention:
`run_<name>_<COMPLETED|FAILED>_<short_id>.json`


```json
{
    "name": "<container_name>",
    "container_id": "<long_container_id>",
    "run_context": {
        "app": "<used_app>",
        "image": "<used_image>",
        "args": {
            ...
        },
        "data_dir": {
            ...
        }
    },
    "completed": "<datetime|null>",
    "failed": "<datetime|null>",
    "started": "<datetime|null>",
    "logs": [
        ...
    ]
```
Logs are extracted from the container, split into single rows and stored as a list.


## Settings
The **Automation App** settings are defined in `./app/settings.py` .
Two settings are available:

- `CHECK_INTERVAL`: sleep interval (in seconds) before the Automation App checks for run status
- `LOG_LEVEL`: log level for the Automation App