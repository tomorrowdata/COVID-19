import json
import logging
import os
from tqdm import tqdm

import time
from collections import deque
from datetime import datetime
from typing import Any, Deque, List, Optional
import re

import docker
from docker.client import DockerClient
from docker.errors import APIError, NotFound
from docker.models.containers import Container
from settings import CHECK_INTERVAL, LOG_LEVEL

import pandas as pd

FORMATTER = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
logging.basicConfig(format=FORMATTER)

SANITIZE_PATTERN = re.compile("[\.,'@;$&\"%?\- ]+")

def get_logger(name: str, log_level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    return logger


def logjson(msg: dict) -> str:
    try:
        return json.dumps(msg, indent=2)
    except Exception as ex:
        return f"STR: {str(ex)}\n" + str(msg)


def get_docker_client() -> DockerClient:
    return docker.DockerClient(base_url="unix://var/run/docker.sock")


def get_automation_conf_json(file_name: str) -> dict:
    with open(os.path.join("./configs/", file_name)) as fp:
        return json.load(fp)


class ContainerIsStillRunningError(BaseException):
    def __init__(self, container: Container, *args: object) -> None:
        super().__init__(*args)
        self.container = container


class RunAlreadyStartedException(BaseException):
    def __init__(self, started: str, *args: object) -> None:
        super().__init__(*args)
        self.start_date = started


def set_config_placeholders(config: dict, placeholder: str, value: str) -> dict:
    config_str = json.dumps(config)
    pattern = re.compile("{}{}{}".format("{", placeholder, "}"))
    config_str_ch = pattern.sub(value, config_str)
    return json.loads(config_str_ch)


def _assert_defined(value: Any) -> Any:
    assert value is not None
    return value


def _sanitize_docker_name(name: str) -> str:
    return SANITIZE_PATTERN.sub("-", name)

def _sanitize_file_name(name: str) -> str:
    return SANITIZE_PATTERN.sub("_", name)


class Run:
    PROGRAM = "python3"
    STATUS_RUNNING = "running"
    STATUS_EXITED = "exited"

    def __init__(
        self,
        run_conf: dict,
        docker_client: DockerClient,
        logger: logging.Logger,
    ) -> None:

        self.name = _sanitize_docker_name(_assert_defined(run_conf.get("name")))
        self._image = _assert_defined(run_conf.get("image"))
        self._app = _assert_defined(run_conf.get("app"))
        self._data_dir = _assert_defined(run_conf.get("data"))
        self._args = _assert_defined(run_conf.get("args"))
        self.log = logger
        self.dc = docker_client

        # state information
        self._started = None
        self._completed = None
        self._failed = None
        # container related info
        self._container_logs = None
        self._container_id = None

        self._remove_if_already_exists()
        self._created = datetime.now().isoformat()

    def _get_container_or_none(self):
        try:
            res: Container = self.dc.containers.get(self.name)
        except NotFound:
            return None
        return res

    def _remove_container(self, container: Container) -> bool:
        try:
            container.remove()
        except APIError:
            return None
        return True

    def _remove_if_already_exists(self):
        # remove the container if exists and is not running
        if (container := self._get_container_or_none()) :
            if container.status != self.STATUS_RUNNING:
                self.log.info(
                    f"Found a previous container {container.name} with id {container.short_id} is in state: {container.status}"
                )
                if self._remove_container(container):
                    self.log.info(
                        f"Removing previous container {container.name} with id {container.short_id}"
                    )
            else:
                self.log.warning(
                    f"Container {container.name} with id {container.short_id} is still running!"
                )
                raise ContainerIsStillRunningError(container)

    def run(self):
        # avoid running twice
        if not self._started:
            self.log.info(f"Running container {self.name} with image {self._image}")

            # add the reference date to the pickleprefix
            self.log.debug(f"Set environment variables:\n{logjson(self._args)}")

            container = self.dc.containers.run(
                image=self._image,
                name=self.name,
                command=f"{self.PROGRAM} {self._app}.py",
                volumes={
                    self._data_dir["source"]: {
                        "mode": "rw",
                        "bind": self._data_dir["target"],
                    }
                },
                environment=self._args,
                detach=True,
            )
            self._started = datetime.now().isoformat()
            self._container_id = container.id
            self.log.info(f"Running container id: {container.short_id}")
        else:
            raise RunAlreadyStartedException(self._started)

    def _get_run_logs(self) -> List[str]:
        if (container := self._get_container_or_none()) and self._started:
            logs_ = container.logs(
                timestamps=True, since=datetime.fromisoformat(self._started)
            )
            logs_ = logs_.decode("utf-8")
            logs_list = logs_.split("\n")
            return logs_list

    def check_ended_update(self) -> bool:
        if self._started and (status := self.status):
            if status != self.STATUS_RUNNING:
                self._completed = datetime.now().isoformat()
                self._container_logs = self._get_run_logs()
                return True
        return False

    def get_run_report(self) -> dict:
        return {
            "name": self.name,
            "container_id": self._container_id,
            "run_context": {
                "app": self._app,
                "image": self._image,
                "args": self._args,
                "data_dir": self._data_dir,
            },
            "completed": self._completed,
            "failed": self._failed,
            "started": self._started,
            "logs": self._container_logs,
        }

    @property
    def status(self) -> Optional[str]:
        # run status matched the container one
        if container := self._get_container_or_none():
            return container.status
        return None

    @property
    def is_failed(self) -> bool:
        return self._failed is not None

    @property
    def failed(self) -> Optional[str]:
        return self._failed

    @failed.setter
    def failed(self, date: str):
        self._failed = date

    @property
    def is_ended(self) -> bool:
        return self._completed is not None

    @property
    def ended(self) -> Optional[str]:
        return self._completed

    @property
    def short_id(self) -> Optional[str]:
        if self._container_id:
            return self._container_id[:10]
        return None

    def __repr__(self) -> str:
        return f"Run(name={self.name}, id={self.short_id}, image={self._image}, ended={self.is_ended})"


class RTAutomation:
    THIS_CONTAINER = "RTAutomation"

    def __init__(
        self,
        docker_client: DockerClient,
        runs_config: dict,
        logger: logging.Logger,
        check_period=30,
    ) -> None:
        self.dc = docker_client
        self.data_dir = _assert_defined(
            runs_config.get("run_data_dir", "./data")
        )
        self.data_prefix = _assert_defined(
            runs_config.get("run_data_prefix", "NA")
        )

        self.max_parallel = _assert_defined(
            runs_config.get("max_parallel_containers", 4)
        )
        self.result_dir = _assert_defined(
            runs_config.get("run_results_dir", "./run_results")
        )
        self.runs = runs_config.get("runs", [])
        self.check_period = check_period

        self._running: Deque[Run] = deque([], maxlen=self.max_parallel)
        self._scheduled: Deque[Run] = deque([])
        self._completed: Deque[Run] = deque([])
        self._failed = []
        self.log = logger
        self._created = datetime.now().isoformat()

        self._schedule_runs()

    def _schedule_runs(self):
        for run_config in self.runs:
            run_name = run_config.get("name", None)
            self.log.info(f"Scheduling run: {run_name}")
            try:
                new_run = Run(run_config, self.dc, self.log)
            except ContainerIsStillRunningError:
                self.log.error(
                    f"Aborting: container for run {run_name} is still running"
                )
                exit(1)
            except Exception as ex:
                self.log.error(f"Aborting: Failed creating instance for run {run_name}")
                exit(2)
            # schedule new run adding them to th
            self._scheduled.appendleft(new_run)

    def _update_running(self) -> None:
        for _ in range(len(self._running)):
            current_run = self._running.pop()
            try:
                current_run.check_ended_update()
            except Exception as ex:
                self.log.error(
                    f"Exception while checking the status for {current_run.name}"
                )
                current_run.failed = datetime.now().isoformat()
                self._failed.append((current_run, ex))
            else:
                self._running.appendleft(current_run)

    def _free_ended(self) -> int:
        ended = 0
        for _ in range(len(self._running)):
            current_run = self._running.pop()
            if current_run.is_ended:
                self.log.info(
                    f"Removing ended run {current_run.name} from running queue"
                )
                self.log.info(
                    f"Adding ended run {current_run.name} into completed list"
                )
                self._completed.append(current_run)
                self._save_report(current_run)
                ended += 1
            elif current_run.is_failed:
                self.log.info(
                    f"Removing failed run {current_run.name} from running queue"
                )
                self._failed.append((current_run, Exception()))
                self._save_report(current_run)
                ended += 1
            else:
                self._running.appendleft(current_run)
        return ended

    def _add_scheduled(self) -> int:
        failed_ = 0
        for _ in range(len(self._scheduled)):
            # take the top element of the queue
            scheduled = self._scheduled.pop()
            if len(self._running) < self.max_parallel:
                self.log.info(f"About to start run: {scheduled.name}")
                try:
                    scheduled.run()
                except Exception as ex:
                    self.log.error(
                        f"Exception while running {scheduled.name} - {ex.__class__.__name__}"
                    )
                    self._failed.append((scheduled, ex))
                    failed_ += 1
                else:
                    # insert on the bottom of the queue
                    self._running.appendleft(scheduled)
            else:
                self.log.info(
                    f"Max parallel number of runs reached! Delaying run: {scheduled.name}"
                )
                # insert on top of the queue
                self._scheduled.append(scheduled)
                break

        return failed_

    def _check_empty_scheduled(self) -> bool:
        still_scheduled = len(self._scheduled)
        self.log.info(f"Number of scheduled runs: {still_scheduled}")
        return still_scheduled == 0

    def _check_empty_running(self) -> bool:
        still_running = len(self._running)
        self.log.info(f"Number of active runs: {still_running}")
        return still_running == 0

    def _wait(self):
        time.sleep(self.check_period)

    def _save_report(self, run: Run):
        status = "FAILED" if run.is_failed else "COMPLETED"
        report_name = f"run_{run.name}_{status}_{run.short_id}.json"
        date_ = self._created.replace(":", "#").split(".")[0]
        save_dir = os.path.join(self.result_dir, date_)
        os.makedirs(save_dir, exist_ok=True)
        path_ = os.path.join(save_dir, report_name)

        self.log.info(f"Saving report to {path_}")
        with open(path_, "w") as fp:
            json.dump(run.get_run_report(), fp)

    def _merge_results(self):
        self.log.info("Merging regions results")
        completed_regions = {
            r._args.get("REGION"): _sanitize_file_name(r._args.get("REGION")) 
            for r in self._completed if r._args.get("REGION")
        }
        DATA_PATH = os.path.join(self.data_dir, "computed/WIP")
        regional_calc_data = None
        for region, region_sanitized in completed_regions.items():
            # TODO fix hardcoded pastdays
            region_pickle_name = os.path.join(
                DATA_PATH,
                f'{self.data_prefix}_futbound_08_12_{region_sanitized}_MCMC_Rt_pastdays_000_000.pickle'
            )
            tempdf = pd.read_pickle(region_pickle_name)
            cols = tempdf.columns.tolist()
            tempdf['Region'] = region
            tempdf = tempdf[['Region']+cols]
            if regional_calc_data is None:
                regional_calc_data = tempdf
            else:
                regional_calc_data = pd.concat((regional_calc_data, tempdf))

        regional_calc_data.sort_values(by=['data', 'Region'], inplace=True)
        regional_calc_data.drop(columns='index', inplace=True)
        regional_calc_data.reset_index(drop=True, inplace=True)
        
        merged_file_name = os.path.join(DATA_PATH, f'{self.data_prefix}_TD_calc_Regions_all_MCMC_Rt.parquet')
        regional_calc_data.to_parquet(merged_file_name)
        self.log.info(f"Merged results saved to {merged_file_name}")

    def __call__(self):
        self.log.info("Start running scheduled runs")
        prog_bar = tqdm(total=len(self._scheduled), desc="Completed Runs")
        while True:
            failed = self._add_scheduled()
            self._wait()
            self._update_running()
            ended = self._free_ended()

            empty_run = self._check_empty_running()
            empty_scheduled = self._check_empty_scheduled()
            prog_bar.update(failed + ended)
            if empty_run and empty_scheduled:
                self.log.info("All runs completed!")
                break

        prog_bar.close()

        self.log.info("Completed runs:")
        for el in self._completed:
            self.log.info(el)

        self.log.info("Failed runs:")
        for el in self._failed:
            run_, ex = el
            self.log.info(f"{run_} - Exception: {ex.__class__.__name__}")

        self._merge_results()


if __name__ == "__main__":
    prefix = os.environ.get("PLACEHOLDER_DATE", None)
    project_dir = os.environ.get("PLACEHOLDER_PROJECT_DIR", None)
    config_file_name = os.environ.get("CONFIG_FILE", None)

    assert prefix is not None
    assert config_file_name is not None
    assert project_dir is not None

    client = get_docker_client()
    config = get_automation_conf_json(config_file_name)
    logger = get_logger("Run Manager", LOG_LEVEL)

    # change config placeholders
    config = set_config_placeholders(config, "DATE", prefix)
    config = set_config_placeholders(config, "PROJECT_DIR", project_dir)

    rt_automation = RTAutomation(client, config, logger, check_period=CHECK_INTERVAL)
    rt_automation()