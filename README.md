# QoS

A short course with code on basics of QoS and QoE.

Please see individual READMEs in subfolders.

## How to install the individual projects and their requirements

### Clone the repo

```bash
$ git clone https://github.com/jrozhon/qos.git
```

This will create a folder named "qos" in your current directory.

Based on the instructions given by the lecturer, go to the appropriate folder, i.e. qos-01.

```bash
$ cd qos-01
```

### Set up a virtual environment

It is considered a best practice to install Python dependencies in the virtual environment to prevent possible changes in the system.

To create one, just issue the following command:

```bash
$ python3.11 -m venv venv
```

This will invoke Python's "venv" module and create a "venv" folder. Inside the folder, there will be all the Python dependencies that we are going to install.

But before we install them, we need to switch ourselves to the virtual environment using the command:

```bash
$ source venv/bin/activate
```

This will activate the environment and change the prompt so that it will be prefixed by "(venv)".

### Install the dependencies and the project

In the folder, there is a "pyroject.toml" file that specifies the project dependencies.

These, together with the current directory's content can be installed using "pip" - Python's package manager.

Just issue the following:

```bash
$ pip install .
```

Now, you are ready to go.
