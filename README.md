# The Quadcopter Project Codebase

## Structure

- `archive/`: Deprecated code and previous results that were deemed ineffective, invalid or improperly recorded.
- `arduino/`: Code for each Arduino.
- `bf-conf/`: Modified betaflight-configurator source to enable control and telemetry with Python.
- `doc/`: Papers related to the physics of the project.
- `src/`: Source code for all python programs.
- `raw/`: All the raw data, in the form of json dumps of the `Data` class.

Within `src`, we have `bf.py` which contains a class that communicates with betaflight-configurator. We also have `live.py` and `rec.py` for actually conducting experiments. They rely on `utils.py` to work, which contains `Arduino`, `Writer`, `Plotter` and `Recorder` classes.

## Use
In order to use this project, one likely needs to prepare a python `venv` (for python dependencies) and use `nvm` to use the correct version of `npm` for `betaflight-configurator`. The configurator will also likely need to be recompiled: Follow README instructions in `bf-conf/`.

## Development
### Branching model
Generally speaking, the main/dev branching is obeyed. `dev` code only goes into `main` when it's tested to be largely working.

## Ideas for further work
There are a few tasks that we did not have time to perform along the way. Some notable examples are listed below.

- For a 9-axes load cell setup capable of resolving components, it is very difficult to make the wires exactly orthogonal. However, we can seek to find a matrix that accounts for the contribution of each load cell to the three components x, y and z. This can be obtained with measuring a few known forces, and using `numpy.lstsq`.