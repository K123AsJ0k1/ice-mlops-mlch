---
technologies: "Controller"
category: "Design and use of technology"
difficulty: "Intermediate"
---

# Controller

## Used material

1. <span id="used-material-1"></span> [Python downloads](https://www.python.org/downloads/)

2. <span id="used-material-2"></span> [How to Install Python on Your System: A Guide](https://realpython.com/installing-python/)

3. <span id="used-material-3"></span> [Getting Started - Installing Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

4. <span id="used-material-4"></span> [Filename too long in Git for Windows](https://stackoverflow.com/questions/22575662/filename-too-long-in-git-for-windows)

5. <span id="used-material-5"></span> [Fixing PowerShell Script Execution Policy Issue When Activating Python venv ](https://dev.to/she11_qa/fixing-powershell-script-execution-policy-issue-when-activating-python-venv-582j)

## Why use Controller?

The self-implemented cluster controller, aka Controller, automates the management of local and cloud Docker Compose Ray clusters. It had the following requirements:

- Maturity requirements: Controller must use SWIFT and Docker Compose CLI via repository pip package functions

- Abstraction requirements: Controller must only require activation to activate or deactivate a Ray cluster based on dictionary conditionals

- Interoperability requirements: Python and Docker must be used to enable simple setup across computers

These features enable the Controller to reduce the manual terminal actions scattered developers need to use remote, local, and cloud Ray clusters on the machines they can access, and they let developers use dictionary conditionals stored in Allas to control the activation and deactivation of these distributed Ray clusters.

## How to use Controller?

Assuming you have setup Python |[(1)](#used-material-1), [(2)](#used-material-2)|, Git [(3)](#used-material-3), and Docker as described in [Docker chapter](../part-1/07_docker.md) on your local or cloud machines, we can make the controller run with the following steps:

1. Download the repository into a suitable folder

```
git clone https://github.com/K123AsJ0k1/ice-mlops-mlch.git
cd multi-cloud-hpc-oss-mlops-platform
```

If you have problems with Windows, use the following to enable cross-platform paths [(4)](#used-material-4):

```
git config --global core.longpaths true
```

2. Move the .env template and .yaml template into .ssh. 

```
cd ice-mlops-mlch/applications/integration/controller
cat env-template.txt
cat input-template.yaml
```

3. Change the .env template into a file named .env-controller and the .yaml template into a file named controller-input.yaml

4. Fill in and confirm the details of the .env with the details mentioned in [SWIFT chapter](../part-5/04_swift.md)

5. Fill the details of the .yaml in the following way

- env_path = absolute path to the .env-controller file
- object_bucket = the bucket used for storing the conditional dictionary
- object_path = the object path used for storing the conditional dictionary
- controller-dimension = choose either local or cloud
- controller-cluster = give the cluster an easy-to-use name
- compose_path = the absolute path to the used Ray cluster compose YAML file
- check_interval = cooldown in seconds between checking the object

6. Create a virtual environment in the controller folder

```
python3 -m venv exp_venv
source exp_venv/bin/activate
pip install -r packages.txt
```

If you have problems with Windows, use the following to enable pip installs [(5)](#used-material-5):

```
python -m venv exp_venv
.\exp_venv\Scripts\activate
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser 
pip install -r packages.txt --no-cache-dir
```

7. Ensure either Docker Desktop or Docker Engine is running

8. Make the controller run

```
ubuntu
python3 run_controller.py --input /home/(your_user)/.ssh/controller-input.yaml

windows
python run_controller.py --input C:\Users\(your_user)\.ssh\controller-input.yaml
```

9. The controller should start printing output to the logs folder. See example logs below:

```
2026-06-29 09:53:28 EEST [INFO] Logging initialized. Archive file created at: /ice-mlops-mlch/applications/integration/controller/logs/run_20260629_095328.log
2026-06-29 09:53:28 EEST [INFO] Starting Ray-Chisel micro-controller
2026-06-29 09:53:28 EEST [INFO] Getting input file
2026-06-29 09:53:28 EEST [INFO] Getting env file
2026-06-29 09:53:28 EEST [INFO] Creating swift parameters
2026-06-29 09:53:28 EEST [INFO] Credential id and secret exist
2026-06-29 09:53:29 EEST [INFO] Setting up swift client
2026-06-29 09:53:29 EEST [INFO] Getting cluster
2026-06-29 09:53:30 EEST [INFO] Checking dict path: local-clusters-lt1
2026-06-29 09:53:30 EEST [INFO] Managing compose file: /ice-mlops-mlch/experiments/deployments/ray/local-laptop-1-ray-cluster-with-chisel-https.yaml
2026-06-29 09:53:30 EEST [INFO] Current state: UNKNOWN
2026-06-29 09:53:30 EEST [INFO] Checking current compose state
2026-06-29 09:53:30 EEST [INFO] Wanted state: False
2026-06-29 09:54:00 EEST [INFO] Checking swift client renewal
2026-06-29 09:54:00 EEST [INFO] Getting cluster
2026-06-29 09:54:01 EEST [INFO] Checking dict path: local-clusters-lt1
```

10. You can now activate or deactivate local and cloud Ray clusters by changing dictionary conditions. See example below:

```
controller_update_dict = {
    'local': {
        'clusters': {
            'lt1': {
                'activate': True
            },
            'lt2': {
                'activate': True
            },
            'lt3': {
                'activate': True
            }
        }
    },
    'cloud': {
        'clusters': {
            'vm2': {
                'activate': False
            }
        }
    }
}

from icebreaker.objects.use import objects_nested_update

update_status = objects_nested_update(
    swift_client = workflow_swift_client,
    storage_parameters = {
        'bucket-target': 'pipeline',
        'bucket-prefix': 'mlch',
        'bucket-user': 'user@example.com',
        'object-name': 'mana',
        'object-serialization': 'pickle',
        'path-replacers': {
            'name': 'local-cloud-cluster.pkl'
        },
        'path-names': [],
        'debug-prints': True,
        'lock-parameters': {},
        'lock-location': None,
        'overwrite': True
    },
    object_input = controller_update_dict
)
```

11. When all workflows have been  run and the Ray cluster has been deactivated, you can stop the controller with 

```
CTRL + C
```

With this, you now have setup automation that enables fast prototyping via JupyterLab by letting you send Ray scripts directly to various Ray clusters, and Kubeflow to activate those clusters to receive Ray scripts and inputs for different pipeline steps described in YAML dictionaries. 

---