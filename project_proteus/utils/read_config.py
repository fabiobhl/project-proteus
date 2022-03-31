#standard libraries import
import json
import os

#package import
from project_proteus import REPO_PATH


def read_config(path=None):
    """
    Function for reading in the config.json file
    """
    #create the filepath
    if path:
        if "config.json" in path:
            file_path = path
        else:
            file_path = os.path.join(path, "config.json")
    else:
        file_path = os.path.join(REPO_PATH, "config.json")
    
    #load in config
    try:
        with open(file_path, "r") as json_file:
            config = json.load(json_file)
    except Exception:
        raise Exception("Your config file is corrupt (wrong syntax, missing values, ...)")

    return config