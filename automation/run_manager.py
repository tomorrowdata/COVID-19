import json
import logging
import os
import time
from collections import deque
from copy import deepcopy
from datetime import datetime
from typing import Deque, List, Optional

import docker
from docker.client import DockerClient
from docker.errors import APIError, NotFound
from docker.models.containers import Container


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


def transform_args_with_modifiers(args: dict, modifiers: dict) -> dict:
    args_copy = deepcopy(args)
    for k in modifiers:
        args_copy[k] = modifiers[k](args_copy[k])
    return args_copy


class Run:
    PROGRAM = "python3"
    STATUS_RUNNING = "running"
    STATUS_EXITED = "exited"

    def __init__(
        self,
        run_conf: dict,
        args_modifiers: dict,
        docker_client: DockerClient,
        logger: logging.Logger,
    ) -> None:

        self.name = run_conf.get("name")
        self._image = run_conf.get("image")
        self._app = run_conf.get("app")
        self._data_dir = run_conf.get("data")
        self._args = run_conf.get("args")
        self.log = logger
        self.dc = docker_client
        self.args_mod = args_modifiers

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
                    f"Container {container.name} with id {container.short_id} is in state: {container.status}"
                )
                if self._remove_container(container):
                    self.log.info(
                        f"Container {container.name} with id {container.short_id} removed"
                    )
            else:
                self.log.error(
                    f"Container {container.name} with id {container.short_id} is still running!"
                )
                raise ContainerIsStillRunningError(container)

    def run(self):
        # avoid running twice
        if not self._started:
            self.log.info(f"Running container {self.name} with image {self._image}")

            # add the reference date to the pickleprefix
            args_ = transform_args_with_modifiers(self._args, self.args_mod)
            self.log.debug(f"Set environment variables:\n{logjson(args_)}")

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
                environment=args_,
                detach=True,
            )
            self._started = datetime.now().isoformat()
            self._container_id = container.id
            self.log.info(f"Running container id: {container.short_id}")
        else:
            raise RunAlreadyStartedException(self._started)

    def _get_run_logs(self) -> List[str]:
        if (container := self._get_container_or_none()) and self._started:
            logs_ = container.logs(timestamps=True, since=datetime.fromisoformat(self._started))
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
        return self._failed is None

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
            return self._container_id[:6]
        return None

    def __repr__(self) -> str:
        return f"Run(name={self.name}, id={self._container_id})"


class RTAutomation:
    THIS_CONTAINER = "RTAutomation"

    def __init__(
        self,
        docker_client: DockerClient,
        runs_config: dict,
        logger: logging.Logger,
        prefix_date: str,
        check_period=30,
    ) -> None:
        self.dc = docker_client
        self.max_parallel = runs_config.get("max_parallel_containers", 4)
        self.result_dir = runs_config.get("run_results_dir", "./run_results")
        self.runs = runs_config.get("runs", [])
        self.arg_modifier = {"PICKLEPREFIX": lambda x: x.format(DATE=prefix_date)}
        self.check_period = check_period

        self._running: Deque[Run] = deque([], maxlen=self.max_parallel)
        self._scheduled: List[Run] = []
        self._completed: List[Run] = []
        self._failed = []
        self.log = logger

        self.schedule_runs()

    def schedule_runs(self):
        for run_config in self.runs:
            run_name = run_config.get("name", None)
            self.log.info(f"Scheduling run: {run_name}")
            try:
                new_run = Run(run_config, self.arg_modifier, self.dc, self.log)
            except Exception as ex:
                self.log.error(f"Failed creating instance for run {run_name}")
                self._failed[(run_name, ex)]

            self._scheduled.append(new_run)

    def _update_running(self):
        for current_run in self._running:
            try:
                current_run.check_ended_update()
            except Exception as ex:
                self.log.error(
                    f"Exception while checking the status for {current_run.name}"
                )
                current_run.failed = datetime.now().isoformat()
                self._failed.append((current_run.name, ex))

    def _free_ended(self):
        for current_run in self._running:
            if current_run.is_ended or current_run.is_failed:
                self.log(f"Removing {current_run.name} from running queue")
                self._running.remove(current_run)
                self.log(f"Adding {current_run.name} into completed list")
                self._completed.append(current_run)

    def _add_scheduled(self):
        for scheduled in self._scheduled:
            if len(self._running) < self.max_parallel:
                self.log.info(f"About to start run: {scheduled.name}")
                try:
                    scheduled.run()
                except Exception as ex:
                    self.log.error(f"Exception while running {scheduled.name}")
                    self._failed.append((scheduled.name, ex))
                else:
                    self._running.appendleft(scheduled)
            else:
                self.log.debug(f"Max parallel level reached! Delaying {scheduled.name}")

    def _check_empty_scheduled(self) -> bool:
        still_scheduled = len(self._scheduled)
        self.log.info(f"Number of scheduled Runs: {still_scheduled}")
        return still_scheduled == 0

    def _check_empty_running(self) -> bool:
        still_running = len(self._running)
        self.log.info(f"Number of active Runs: {still_running}")
        return still_running == 0

    def _wait(self):
        time.sleep(self.check_period)

    def save_report(self, run: Run):
        status = "FAILED" if run.is_failed else "COMPLETED"
        time_ = run.ended or run.failed

        report_name = f"run_{run.name}_{status}_{time_}_{run.short_id}.json"
        path_ = os.path.join(self.result_dir, report_name)

        self.log.info(f"Saving report to {path_}")
        with open(path_, "w") as fp:
            json.dump(run.get_run_report(), fp)

    def __call__(self):
        self.log.info("Start running scheduled runs")
        while not (self._check_empty_running() and self._check_empty_scheduled()):
            self._add_scheduled()
            self._wait()
            self._update_running()
            self._free_ended()

        self.log.info(f"Completed!\n")
        self.log.info("Completed runs:")
        for el in self._completed:
            self.log.info(el.name)

        self.log.info(f"\n")
        self.log.info("Failed runs:")
        for el in self._failed:
            self.log.info(el[0])


if __name__ == "__main__":
    prefix = os.environ.get("PREFIX_DATE", None)
    config_file_name = os.environ.get("CONFIG_FILE", None)
    assert prefix is not None
    assert config_file_name is not None

    client = get_docker_client()
    config = get_automation_conf_json(config_file_name)
    logger = get_logger("Run Manager", logging.DEBUG)

    rt_automation = RTAutomation(client, config, logger, prefix, check_period=10)
    rt_automation()