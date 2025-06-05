import os
import yaml
import argparse

current_file = os.path.abspath(__file__)
PROJ_PATH = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
CONFIG_PATH = os.path.join(PROJ_PATH, "config.yaml")

"""
Loads config file containing default configurations
"""
def load_config():
    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)
    
"""
Parses command line arguements
"""
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", type=str)
    parser.add_argument("--allarchives", action="store_true")
    
    return parser.parse_args()

"""
Modified config based on command line arguements
"""
def build_final_config(config, args):
    final_config = config.copy()
    
    if args.username:
        final_config["username"] = args.username

    if args.allarchives:
        final_config["all_archives"] = "True"

    return final_config

raw_config = load_config()
args = parse_args()

# Initialize config
config = build_final_config(raw_config, args)


