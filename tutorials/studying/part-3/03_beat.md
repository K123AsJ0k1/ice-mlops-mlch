---
technologies: "Beat"
category: "Choice and use of technology"
difficulty: "Intermediate"
---

# Beat

## Used material

1. <span id="used-material-1"></span> [Run Redis on Docker](https://redis.io/docs/latest/operate/oss_and_stack/install/install-stack/docker/)

2. <span id="used-material-2"></span> [Redis pip package](https://pypi.org/project/redis/)

3. <span id="used-material-3"></span> [Celery pip package](https://pypi.org/project/celery/)

4. <span id="used-material-4"></span> [Celery periodic tasks](https://docs.celeryq.dev/en/latest/userguide/periodic-tasks.html)

5. <span id="used-material-5"></span> [Celery beat](https://docs.celeryq.dev/en/stable/reference/celery.beat.html)

6. <span id="used-material-6"></span> [Celery tasks](https://docs.celeryq.dev/en/main/userguide/tasks.html)

7. <span id="used-material-7"></span> [Celery periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)

## Why use Beat?

Beat was chosen for the following reasons:

- Most common task scheduler for Celery (maturity)

- Easy setup and creation of looping task execution (abstraction)

- Usable in any place where Python can be used (interoperable)

These enable us to use Beat to create a decoupled scheduler to run periodic tasks in Celery containers.

## How to use Beat?

Assuming we have a running Redis container [(1)](#used-material-1), a running Celery instance setup with [Celery chapter](./01_celery.ipynb), and a running Flower monitor setup with [Flower chapter](./02_flower.ipynb), we can start the Beat scheduler by setting up a venv |[(2)](#used-material-2),[(3)](#used-material-3)| and executing [run](./beat/run_beat.py) in the following way |[(4)](#used-material-4),[(5)](#used-material-5)|:

```
cd beat
python3 -m venv beat_venv
source beat_venv/bin/activate
pip install -r packages.txt
python3 run_beat.py
```

Now, you can check http://127.0.0.1:7501/tasks to see that the beat configuration (see row 41) in setup beat requests every 40 seconds to have the Celery instance run submitter-trigger. This is defined in run beat using the SCHEDULER_TIMES environmental variable, with ‘|’ as the delimiter, which enables us to change scheduler times in containers as needed. When we want the scheduling to stop, we simply need to stop Beat from running, which allows us to use or debug the entire stack of fastapi-celery-flower without any effect.

## Beat file structure

When you check the files inside the beat folder, you notice the following structure:

- [run_beat](./beat/run_beat.py)
- [setup_beat](./beat/setup_beat.py)
- [packages](./beat/packages.txt)

The purpose of this structure is to keep things as simple as possible, since the software only requires a few small functions and minimal configuration to be useful.

## Beat scheduling considerations

Finding the correct time for a Celery task depends on the execution time, set constraints, and task function. For our use case, execution times are in the minute range, the main constraint is minimizing impact on the target systems, and the tasks serve as interactive pathways for inputs and outputs. Therefore, our times are roughly 15-60 seconds, depending on how willing we are to wait. 

Our locking code ensures serial execution of code, but shorter times result in more useless rows in Flower metrics, which we can reduce by setting a rate limit on scheduled tasks [(6)](#used-material-6). For example, we could set ‘4/m’ or ‘1/m’ (see row 19) for the [submitter-trigger](./celery/tasks/scheduled/trigger.py) to achieve our desired range. Be aware that rate-limited tasks are not ignored; they are placed in a backlog, which means bad configuration can lead to stale tasks.

## Important parts of Beat

The most important parts to keep an eye on when trying to understand or develop a Beat scheduling are [(7)](#used-material-7):

- Entry = Name of the scheduling configuration (see use in [setup beat](./beat/setup_beat.py) row 39)
- Task = Name of the scheduled task (see use in [setup beat](./beat/setup_beat.py) row 40)
- Schedule = Scheduling time in seconds (see use in [setup beat](./beat/setup_beat.py) row 41)
- Arguments = Given parameters to task (see use in [setup beat](./beat/setup_beat.py) row 42)
- Relative = Scheduling by the clock (see use in [setup beat](./beat/setup_beat.py) row 43)
- Expire seconds = Seconds for the task to be ignored (see use in [setup beat](./beat/setup_beat.py) row 45)

---