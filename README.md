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

Either start a Jupyter notebook and load DemoInterface2.ipynb

Or from a terminal run:
```bash
panel serve --show DemoInterface2.ipynb
```

### Heroku deploy

To access the heroku deployment navigate to https://movingmast.herokuapp.com   
Note that Heroku can take a few minutes to start the app for the first time.