from requests import Response, session
from typing import Union
from time import sleep
import logging
import json

from distcompute_client.errors import *

logging.basicConfig(format="[distcompute-client] %(asctime)s - %(message)s", datefmt="%H:%M", level=logging.INFO)

def log(message) -> None:
    logging.info(message)

def verbose_log(message) -> None:
    print(f"[distcompute-client] - {message}")

# The main client instance.
class Client(object):
    def __init__(self, url: str, stage: str, nickname: str, verbose: bool = True) -> None:
        if url[-1] == "/":
            url = url[:-1]
        
        self.s = session()
        self.url = url
        self.stage = stage
        self.nickname = nickname
        self.verbose = verbose
        
        self.token = None
        self.project = "N/A"
        self.display_name = "N/A"
        self.stage_name = "N/A"
        
        if self.verbose:
            self.log_fn = verbose_log
        else:
            self.log_fn = log

        if self.verbose:
            self.log_fn("connecting to tracker...")
        
        params = {
            "nickname": self.nickname,
            "stage": self.stage
        }

        r = self._request("GET", "/api/new", params=params)

        err = self._handle_exceptions(r)
        if err:
            self.log("Crashed", _err=True)
            raise err
        
        data = r.json()
        self.token = data["token"]
        self.display_name = data["display_name"]
        self.project = data["project"]
        self.stage_name = data["stage_name"]
        
        self.job = None
        self.job_id = None
        
        if self.verbose:
            self.log_fn(f"{self.project} - connected to tracker server")
            self.log_fn(f"{self.project} - joined project: {self.project}")
            self.log_fn(f"{self.project} - worker name: {self.display_name}")
            self.log_fn(f"{self.project} - you can view this worker's progress at the following url:")
            self.log_fn(f"{self.project} - {self.url}/worker/{self.stage_name.lower()}/{self.display_name}")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Response:
        try:
            return self.s.request(method, self.url + endpoint, **kwargs)
        except Exception as e:
            if self.verbose:
                self.log_fn(f"{self.project} - retrying request after {e} error...")
            sleep(15)
            return self._request(method, endpoint, **kwargs)

    def _handle_exceptions(self, r: Response) -> Union[Exception, None]:
        if r.status_code == 200:
            return None
        elif r.status_code == 400:
            return ValueError(f"[distcompute-client] {r.text} (status {r.status_code})")
        elif r.status_code == 403:
            return ZeroJobError(f"[distcompute-client] {r.text} (status {r.status_code})")
        elif r.status_code == 404:
            return WorkerTimedOutError(f"[distcompute-client] {r.text} (status {r.status_code})")
        else:
            return ServerError(f"[distcompute-client] {r.text} (status {r.status_code})")
    
    # Fetches the number of remaining jobs for the worker's stage.
    def job_count(self) -> int:
        params = {
            "stage": self.stage
        }

        r = self._request("GET", "/api/jobCount", params=params)

        err = self._handle_exceptions(r)
        if err:
            self.log("Crashed", _err=True)
            raise err

        count = int(r.text)
        
        if self.verbose:
            self.log_fn(f"{self.project} - jobs remaining: {count}")

        return count
    
    # Makes the node send a request to the tracker, asking for a new job.
    def new_job(self) -> None:
        self.log_fn(f"{self.project} - looking for new job...")

        body = {
            "token": self.token
        }

        r = self._request("POST", "/api/newJob", json=body)

        err = self._handle_exceptions(r)
        if err:
            self.log("Crashed", _err=True)
            raise err
        
        data = r.json()
        self.job = data["data"]
        self.job_id = data["number"]

        if self.job.startswith("<!json!>"):
            self.job = json.loads(self.job[8:])
            
        if self.verbose:
            self.log_fn(f"{self.project} - recieved new job #{self.job_id}")

    # Marks a job as completed/done.
    def complete_job(self, data: Union[str, list, dict]) -> None:
        if isinstance(data, (dict, list)):
            data = "<!json!>" + json.dumps(data)
        elif not isinstance(data, str):
            raise ValueError("data must be one of: str, list, dict")
        
        body = {
            "token": self.token,
            "data": data
        }

        r = self._request("POST", "/api/completeJob", json=body)
        self.job = None
        self.job_id = None
        
        err = self._handle_exceptions(r)
        if err:
            self.log("Crashed", _err=True)
            raise err
        
        
        if self.verbose:
            self.log_fn(f"{self.project} - marked job as complete")

    # Logs the progress string to the tracker.
    def log(self, progress: str, _err: bool = False) -> None:
        body = {
            "token": self.token,
            "progress": progress
        }

        r = self._request("POST", "/api/updateProgress", json=body)

        err = self._handle_exceptions(r)
        if err and not _err:
            self.log("Crashed", _err=True)
            raise err
        
        if self.verbose and not _err:
            self.log_fn(f"{self.project} - logged new progress data: {progress}")
    
    
    # Returns True if the worker is still alive (not timed out), otherwise returns False.
    def is_alive(self) -> bool:
        body = {
            "token": self.token
        }

        r = self._request("POST", "/api/validateWorker", json=body)

        err = self._handle_exceptions(r)
        if err:
            self.log("Crashed", _err=True)
            raise err
        
        return ("True" in r.text)

    # Reports data made by previous worker as invalid. If this repeatedly occurs, the job is re-opened for workers at the previous stage.
    def flag_invalid_data(self) -> bool:
        body = {
            "token": self.token
        }

        r = self._request("POST", "/api/flagInvalidData", json=body)
        self.job = None
        self.job_id = None

        err = self._handle_exceptions(r)
        if err:
            self.log("Crashed", _err=True)
            raise err
    
    # Removes the worker instance from the server, re-opening any pending jobs.
    def bye(self) -> None:
        body = {
            "token": self.token
        }

        self._request("POST", "/api/bye", json=body)
        self.job = None
        self.job_id = None

        # No need for error checking as client may already be disconnected.

        if self.verbose:
            self.log_fn(f"{self.project} - closed worker")


# Creates and returns a new client instance.
def init(
    url: str,
    stage: str,
    nickname: str = "anonymous",
    verbose: bool = True
) -> Client:
    stage = stage.lower()[0]
    
    return Client(
        url=url,
        stage=stage,
        nickname=nickname,
        verbose=verbose
    )
