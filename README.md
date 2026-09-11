# Quality of Service and Quality of Experience

Course material for *Quality of Service and Quality of Experience* (QoS & QoE), taught at the Faculty of Electrical Engineering and Computer Science, VSB – Technical University of Ostrava. The course introduces the properties of signals and network traffic that determine the perceived quality of multimedia services, and the mechanisms networks use to control them.

Each exercise is a self-contained directory with a `README.md` covering the theory and a Jupyter notebook containing the practical tasks. Exercises are intended to be worked through in order.

## Exercises

| Exercise | Topic | Tools |
|---|---|---|
| [01](qos-01/README.md) | Signals, pulse-code modulation, Gaussian noise, and channel capacity | Jupyter |
| [02](qos-02/README.md) | Probability distributions, the Poisson process, and M/M/1 queueing systems | Jupyter |
| [03](qos-03/README.md) | Network traffic properties and their effect on QoE: packet crafting, VoIP, traffic control | Jupyter, Wireshark, `tc` |
| [04](qos-04/README.md) | Objective image quality metrics: PSNR and SSIM | Jupyter |
| 05 | Software-defined network emulation in Mininet | Mininet |
| 06 | Mininet: topologies, link parameters, and performance testing | Mininet |
| [07](qos-07/README.md) | Quality of Service in networks: marking, shaping, and queueing disciplines | Mininet |

All exercises are carried out on the laboratory servers, accessed over SSH.

## Prerequisites

- Python 3.12 or newer.
- [`uv`](https://docs.astral.sh/uv/), which manages virtual environments and dependencies for each exercise. Installation instructions are in the `uv` documentation.
- Git.
- SSH access to the laboratory servers, on which all exercises are run. Addresses and credentials are distributed through the LMS.
- For Exercise 03, Wireshark and the ability to run commands as root or to set Linux capabilities; details are given in the exercise README.

## Setting up an exercise

Log in to a laboratory server over SSH and clone the repository once.

```bash
git clone https://github.com/jrozhon/qos.git
```

Each exercise directory contains its own `pyproject.toml`, so the environment is created per exercise. Change into the exercise directory and synchronize it; this creates a virtual environment in `.venv` and installs the pinned dependencies.

```bash
cd qos/qos-01
uv sync
```

Start JupyterLab from within the same directory. The server is bound to all interfaces so that it can be reached from the local browser.

```bash
uv run jupyter lab --ip 0.0.0.0
```

JupyterLab prints a URL containing an access token; replace its host part with the address of the laboratory server and open it in a local browser. Notebooks are located in the `qos_NN/` package directory of each exercise and expect to be opened from there, because they import helper code from the adjacent `lib/` directory.

> [!NOTE]
> The `pyproject.toml` files are provided. For independent projects, `uv init` creates a new one; that step is not needed in this course.

### Adding a package

Additional libraries are added to the current exercise only.

```bash
uv add numpy pandas
```

`uv` installs the package and records it in `pyproject.toml`. If `pyproject.toml` is edited by hand, run `uv sync` again to apply the change.

## Repository layout

```
qos-NN/
├── README.md          theory and task description for the exercise
├── pyproject.toml     dependencies, managed by uv
├── fig/               figures referenced from the README
└── qos_NN/
    ├── exercise_NN.ipynb
    ├── logo.png       university symbol used as a figure watermark
    └── lib/
        ├── core.py    reference implementations and simulation components
        └── params.py  shared matplotlib style
```

Exercises 05–07 contain only a notebook because their tasks are executed in the Mininet command line rather than in Python.

## Contributing

Style conventions for text, equations, figures, and code are defined in [`STYLE.md`](STYLE.md). Contributions should follow them.

## License

Released under the terms of the [MIT License](LICENSE).
