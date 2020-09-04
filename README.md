# Searching Moving Targets at MAST

Prototype interface/workflow to search for moving targets in the MAST Archive

[Google Doc for Notes](https://docs.google.com/document/d/1qwf77xCSwzWCMoCR8HzkH3T0KvMJAZAH9Ra805c5s20)

![](https://img.shields.io/badge/Made%20at-%23AstroHackWeek-8063d5.svg?style=flat)

### Create repository conda environement

From top level directory:

```bash
conda env create -f env.yml
```

Then activate this environment as:

```bash
conda activate moving-mast
```

### Run it

Either start a Jupyter notebook and load either DemoInterface2.ipynb or MastDashboard.ipynb

Or from a terminal run:
```bash
panel serve --show MastDashboard.ipynb
```

### Web deploy

You can also launch the notebook with binder:
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/dr-rodriguez/MovingMast/main?filepath=DemoInterface2.ipynb)

There is also a Heroku which you can access at https://movingmast.herokuapp.com   

Note that these web deploys can take a few minutes to start up for the first time.
