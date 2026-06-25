---
technologies: "Python"
category: "Explanation and use of technology"
difficulty: "Easy"
---
 
# Python

## Used material

1. <span id="used-material-1"></span> [Python Pip user guide](https://pip.pypa.io/en/latest/user_guide/)

2. <span id="used-material-2"></span> [Pip install version guide](https://builtin.com/articles/pip-install-specific-version)

3. <span id="used-material-3"></span> [Python Conda user guide](https://docs.conda.io/projects/conda/en/stable/user-guide/getting-started.html)

## Why use Python?

Python is widely used for the following reasons:

- One of the most used programming languages in ML (mature)

- Syntax is simpler compared to options like C and C++ (abstracted)

- Widely supported by local, cloud, and HPC platforms (interoperable)

These make Python the default language for ML developers seeking reduced friction when creating ML applications.

## How to use Python?

In our use case we interact with Python in the following ways [(1)](#used-material-1):

- Creating virtual environments

```
python3 -m venv (venv_name)
```

- Activating virtual environments

```
source (venv_name)/bin/activate
```

- Installing python packages

```
pip install (package)
pip install -r requirements.txt
```

- Creating enviroment requirements

```
pip freeze >> packages.txt
```

## Python package configuration

Configuring PIP packages requires identifying the current packages, listing the required packages, switching package versions, and confirming version compatibilities. 

Package identification is done by checking the packages.txt. It shows a long list of all packages and their versions, which is useful for debugging, but usually too specific for installation. 

Listing the required packages is done by writing down requirements.txt using the PyPI website for the packages your code imports. For example, if we check the following websites (20.3.2025):

- https://pypi.org/project/fastapi/

- https://pypi.org/project/uvicorn/

- https://pypi.org/project/celery/

- https://pypi.org/project/redis/

We can form the following requirements.txt list:

```
fastapi==0.135.1
uvicorn==0.42.0
celery==5.6.2
redis==7.3.0
```

This can be used to switch package versions by downgrading or upgrading a package when a package causes dependency problems. PIP usually provides good enough error messages that specify what packages are causing the problems. Package versions can be changed in the following way [(2)](#used-material-2):

```
pip uninstall (package)
pip install (package)==(version)
```

It might also be that the Python version is incompatible with the packages you want to run. In such cases, you either need to downgrade the package, consider other ways to get the functions you want, or use conda to run a specific Python version [(3)](#used-material-3).

---