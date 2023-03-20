# DistCompute Client Library
[![Discord Chat](https://img.shields.io/discord/823813159592001537?color=5865F2&logo=discord&logoColor=white)](https://discord.gg/nRt84U6WaF)

<p align="center">
    <br>
   <img src="https://raw.githubusercontent.com/TheoCoombes/Distributed-Compute-Tracker/main/cdn/example.png" width="550"/>
   <br>
   LAION-5B Workflow Diagram
   <br><br>
</p>

Client library for the tracker previously powering LAION's distributed compute network for filtering commoncrawl with CLIP to produce the LAION-400M and LAION-5B datasets. The previous code has now repurposed as a general-use multi-layer distributed compute tracker and job manager, with added support for a frontend web server dashboard, user leaderboards and up to 5 sequential stages of workers for each job.
* Tracker Server Repo: [TheoCoombes/distcompute-tracker](https://github.com/TheoCoombes/distcompute-tracker)
* LAION-5B Paper: [https://arxiv.org/abs/2210.08402](https://arxiv.org/abs/2210.08402)

# Prerequisites
* Python >= 3.7
* Live tracker server with public URL/IP and a populated jobs database.

# Installation
You can install the distcompute-client library using the following command:
```
pip install distcompute-client
```
Now, from the current directory, you can import the module:
```py
import distcompute_client as dc

client = dc.init(url="https://tracker.example.com/", stage="a")
print(client.display_name)
print(client.project_name)

>>> "hematin-hanking-71"
>>> "LAION-5B"
```

# Methods

## distcompute_client.init(url: str, stage: str, nickname: str = "anonymous", verbose: bool = True) -> Client
Creates and returns a new client instance.
* `url`: the public URL / IP address of the hosted tracker server
* `stage`: the stage for this worker's specific task (a/b/c/d/e)
    - For example, for creating a web-scale dataset, you could use stage "a" for scraping web content, "b" for downloading scraped content, "c" for filtering downloaded content, etc.
    - The output data created from each stage of the cycle is the input given to the next stage's workers.
    - If you would like a linear `input -[worker]-> output` workflow, only stage "a" should be enabled in the tracker.
* `nickname`: provides a machine/user/company-level identifier for this client (default: "anonymous")
    - E.g. "John Doe", "AWS Pod 3" or "LAION".
    - This feature was during the creation of LAION-400M to reward people with their names & contributions on the leaderboard, but can also be used for any general purpose, such as monitoring workers distributed over different pods on AWS.
* `verbose`: enable console messages (default: true)

# Client Reference
```py
import distcompute_client as dc
import time

client = dc.init(
    url="https://example.com/",
    stage="b",
    nickname="Cluster 2 on AWS",
    verbose=True
)

while client.is_alive():
    # Wait for new jobs to appear
    if client.job_count() == 0:
        time.sleep(30)
        continue
    
    client.new_job()
    job_data = client.job # Could be a str/list/dict, depending on what is set by the tracker for stage A, or worker scripts for later stages.
    job_id = client.job_number
    
    while doing_work:
        # ... process data

        client.log("Analysed x / y images") # Updates the worker's progress to the server

    # Report data as invalid to the tracker, look for a new job.
    if some_error:
        client.flag_invalid_data()
        continue
    
    # This becomes input for workers operating at the next stage, "d".
    output = {"file": "s3://job_12345.tar", "total_scraped": 123}

    client.complete_job(output)

# Disconnect from tracker.
client.bye()
```

## Client.job_count() -> int
Returns the number of open jobs at the same stage as the client.
* Note: As jobs are dynamically created, there may be periods of time when your workers don't have any open jobs to fufil. Therefore, you can make use of `Client.job_count()` to detect these periods of inactivity.

## Client.new_job() -> None
Retrieves a new job from the tracker, storing data as class attributes (see below).
* raises a `distcompute_client.errors.ZeroJobError` when there are no jobs open to fufil.

## Client.complete_job(data: Union[str, list, dict]) -> None
Marks the current job as done to the server, and submits data to be passed as an input to workers at the next stage of the project workflow. If there are no more stages remaining, the job is closed.
* `data` (required): data to be passed as an input to workers at the next stage of the project workflow, equivalent to `client.job`.

## Client.log(progress: str) -> None
Logs the progress string `progress` to the server. The status of each worker can then be clearly viewed on the tracker's dashboard.
* `progress` (required): The string detailing the progress, e.g. `"12 / 100 (12%)"`

## Client.is_alive() -> bool
Returns `True` if the worker is still connected to the tracker, and has not timed out, otherwise returns False.

## Client.flag_invalid_data() -> None
Reports the input data (`client.job`) made by previous worker as invalid. If this repeatedly occurs, the job is re-opened for workers at the previous stage.

## Client.bye() -> None
Removes the worker instance from the server, re-opening any pending jobs.

## Client Variables

### Client.job: Union[str, list, dict]
Input data to be processed by the worker. Could be a str/list/dict, depending on what is set by the tracker for stage A, or worker scripts for later stages.

### Client.job_number: int
The job ID set by the tracker, as an incrementing integer (job #1 = 1). Useful when naming/storing files related to each job.

### Client.display_name: str
The display name for this worker on the tracker.

### Client.project: str
The name of the tracker's defined project name, e.g. "LAION-5B".

### Client.stage_name: str
The name of the tracker's stage in the project workflow, e.g. "CPU" or "Scraper".
