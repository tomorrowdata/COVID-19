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