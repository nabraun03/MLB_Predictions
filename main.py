import statsapi
import pandas as pd
import json
from datetime import date, timedelta
import mlbstatsapi
from util import (
    merge_team_stats,
    add_identifying_fields_to_dict,
    add_player_stats,
    print_object_fields,
)
import numpy as np
from statutil import reconstruct_lost_team_stats
import subprocess


def run_scripts(scripts):

    for script in scripts:
        subprocess.run(["python", script])


if __name__ == "__main__":

    scripts = ["apirequests.py", "preprocessing.py"]
    run_scripts(scripts)
