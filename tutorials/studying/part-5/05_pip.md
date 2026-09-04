---
technologies: "pip"
category: "Choice and use of technology"
difficulty: "Intermediate"
---

# Pip

## Used material

1. <span id="used-material-1"></span> [Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)

2. <span id="used-material-2"></span> [How to create a Python package and publish it on GitHub](https://medium.com/@thomas.vidori/how-to-create-a-python-package-and-publish-it-on-github-eebc78b2a12d)

## Why use Pip? 

The Python Pip is the default package manager in Python tools for the following reasons:

- Provides standardized library integration, a robust resolution engine, and a secure distribution infrastructure (mature)

- Easy-to-use venv isolation management, dependency declarations, and a unified interface for different package sources (abstracted)

- Widely supports cross-language packages, various artifact repositories, and used standards ensure utilization across versions (interoperable) 

These features make Pip the default way to package code for automation and scripts, enabling us to centralize global function development in one place while reducing the need to recreate code across the operation.

## How to use Pip?

In our use case, we will develop a locally used Pip package that we can later share using GitHub |[(1)](#used-material-1), [(2)](#used-material-2)|. Assuming you have downloaded your GitHub repository, we can do this in the following way:

1. Create a package folder in the repository

```
cd (suitable-repository-path)
mkdir packages
cd packages
mkdir (package-name)
```

2. Add the following files to the package folder

```
.gitignore
LICENSE
pyproject.toml
```

3. Add the following lines to .gitignore

```
__pycache__
(package-name).egg-info
```

4. Add a suitable license text (such as MIT) to LICENSE

5. Add the following example lines to pyproject.toml

```
[project] 
name = "(package-name)r"
version = "0.0.1"
description = "(package description)"
dependencies = [
    "pydantic"
]

[tool.setuptools.packages.find]
where = ["src"]

[project.optional-dependencies]

swift = [
    "python-swiftclient",
    "keystoneauth1",
    "python-keystoneclient"
]

all = [
    "icebreaker[swift]"
]
```

6. Create src/(package-name)

7. Add __init__.py into the folder with following

```
# src/(package-name)/__init__.py

__version__ = "0.0.1"
```

8. Create a function folder with __init__.py containing the following

```
# src/(package-name)/misc/__init__.py
```

9. Create a function file with lazy imports (enables choosing package dependencies)

```
# src/(package-name)/misc/general.py
def set_formatted_user(
    user: str   
) -> any:
    try:
        import re
    except ImportError as e:
        raise ImportError("misc/Failed to import", e)
    return re.sub(r'[^a-z0-9]+', '-', user)
```

10. When all functions are organized, you can test the package locally (here -e ensures automatic updates)

```
pip install -e ".[all]"
```

11. If there are problems, you can uninstall the package with

```
pip uninstall (package-name)
```

12. When you have pushed the code into a GitHub repository, you can use it anywhere with Pip with the following command

```
pip install (package-name)[swift] @ git+https://github.com/(repository-path).git@(branch-name)#subdirectory=(suitable-repository-path)
```

With this, you can use the package stored in this repository in 3 ways:

1. Download the repository and go to the path with an active venv

```
cd applications/packages/icebreaker
pip install -e ".[all]"
```

2. Download the package from the repository

```
pip install icebreaker[all] @ git+https://github.com/K123AsJ0k1/ice-mlops-mlch.git@main#subdirectory=applications/packages/icebreaker
```

3. Use packages.txt to download the package from the repository

```
icebreaker[all] @ git+https://github.com/K123AsJ0k1/ice-mlops-mlch.git@main#subdirectory=applications/packages/icebreaker
```

From these, we will mainly use 2 and 3 to use the package in various local, cloud, and HPC environments.

---