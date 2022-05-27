import os
import sys
import codecs
import json
from configparser import ConfigParser


def load_parameters(param, dur, climate, rain, inf, sc, leach, steady_state):
    cfg = ConfigParser()
    fn = os.path.split(sys.executable)
    if fn[1].lower().startswith('python'):
        exedir = os.path.abspath(os.path.split(sys.argv[0])[0])
    else:
        exedir = fn[0]
    inipath = os.path.join(exedir, 'yasso.ini')
    cfg.read_file(codecs.open(inipath, "r", "utf8"))
    debug_param = cfg.get("debug", "debug")
    if debug_param.lower() == 'true':
        obj = [
            {'param': param},
            {'dur': dur},
            {'temp': climate},
            {'rain': rain},
            {'inf': inf},
            {'sc': sc},
            {'leach': leach},
            {'steady_state': steady_state}
        ]
        with open('parameters.txt', 'a') as f:
            json.dump(obj, f, indent=4)
