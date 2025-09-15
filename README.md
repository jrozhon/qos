# 🚦 QoS & QoE: The Code Course

Welcome! 👋 This project is your hands-on guide to the essentials of Quality of Service (QoS) and Quality of Experience (QoE).

Dive into the subfolders to find the code and experiments for each lesson. Let's get your environment set up!

## 🚀 Getting Started: The `uv` Way!

We'll be using `uv`, a lightning-fast Python package manager that replaces `pip` and `venv`. It's all you need to get up and running in seconds.

### Step 1: Clone the Codebase 📂

First, get the project files onto your machine. Open your terminal and run:

```bash
git clone https://github.com/jrozhon/qos.git
```

This creates a `qos` directory. Now, navigate into the folder for the lesson you're working on.

```bash
# Example for the first lesson
cd qos/qos-01
```

### Step 2: Power Up Your Environment ⚡️

Now, let's create an isolated environment and install the project dependencies. The `pyproject.toml` file in this project already defines everything you need.

Run the following command to sync your environment. This will create a virtual environment and install the exact package versions specified in the project.

```bash
# Create environment and install dependencies
uv sync
```

> **Note:** For your own future projects, you can create a new `pyproject.toml` file from scratch by running `uv init`. However, for this course, the file is already provided for you.

### Step 3: Launch Jupyter Lab 🛰️

You're all set! To run the notebooks, you'll likely be on a remote lab computer, so you need to make Jupyter accessible. Use the `uv run` command:

```bash
# Run Jupyter Lab and make it accessible from any IP address
uv run jupyter lab --ip 0.0.0.0
```

Jupyter will give you a URL to open in your web browser. Happy coding!

## ✨ Pro-Tip: Adding More Packages

Need an extra library for your experiments? Adding it with `uv` is a breeze.

```bash
# Example: Add the numpy and pandas packages
uv add numpy pandas
```

That's it! `uv` will handle the installation and update your `pyproject.toml`. Remember to re-run `uv sync` if you add packages manually to the `pyproject.toml` file!
