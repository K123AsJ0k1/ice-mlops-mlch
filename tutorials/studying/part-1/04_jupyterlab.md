---
technologies: "JupyterLab"
category: "Choice and use of technology"
difficulty: "Easy"
---

# JupyterLab
 
## Used material

1. <span id="used-material-1"></span> [Installing Jupyter](https://jupyter.org/install)

2. <span id="used-material-2"></span> [Jupyter magic commands](https://ipython.readthedocs.io/en/9.2.0/interactive/magics.html)

## Why use JupyterLab?

JupyterLab was chosen for the following reasons:

- Enables easy documentation, code testing, and network interactions (mature) 

- Simple interactions with code and integration with IDEs (abstracted)

- Widely used and supported by local, cloud, and HPC platforms (interoperable)

These enable us to use JupyterLab as a development environment for documented, iterative, and interactive coding.

## How to use JupyterLab?

To run the JupyterLab server [(1)](#used-material-1), we need to setup an environment and start it up with the following:

```
python3 -m venv part_1_venv
source part_1_venv/bin/activate 
pip install -r packages.txt
jupyter lab
```

When JupyterLab starts, it should open a window in the chosen default browser at the file path where it was activated. You can shut it down with:

```
CTRL + C
Y
```

## Python packages in JupyterLab

JupyterLab uses the packages that the venv had at the time of activation, which means package installations require a restart to take effect. Shutting down can mean losing data, which is why you should be saving just in case before shutting down the server.

## JupyterLab Magic commands

Magic commands are shortcut commands we can use to control the notebook environment or the host system [(2)](#used-material-2). In our case, the most important ones are:

```
%%writefile = writes a file

%run = runs a Python file

!(command) = runs a terminal command
```

## Function initialization in JupyterLab

We can use functions defined outside the notebook by using %run in the following way:

```
%run (absolute_file_path)
```

This can be done again if you modify the code file, but be aware that there are some specific cases, such as errors, that might require you to shut down the kernel for the changes to take effect. JupyterLab enables
easy kernel shutdown with the following:

1. Find kernel tab
2. Click shut down kernel
3. Click restart kernel

---