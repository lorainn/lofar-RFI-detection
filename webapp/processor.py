# webapp/processor.py

import threading
import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lofarimaging.rfi_tools.realtime import read_blocks
from webapp import state
import config


# Logging setup
logger = logging.getLogger("lofar")


def start_observation():
    input_path = state.config["folder"]
    output_path = config.IMAGES_FOLDER

    # NOTE: Output and temp directory are set to Flask's static folder for image visibility
    state.create_observation_directory(base_dir=output_path)
    temp_dir = os.path.join(state.observation_path, "images")

    step = state.config["step"]
    max_threads = state.config["threads"]
    height = state.config["height_m"]

    extent_m = state.config["extent"]
    extent = [-extent_m, extent_m, -extent_m, extent_m]
    x_width = extent[1] - extent[0]
    y_height = extent[3] - extent[2]
    max_range = max(x_width, y_height)
    pixels_per_metre = 150 / max_range

    def run():
        read_blocks(
            input_path=input_path,
            output_path=state.observation_path,
            caltable_dir=config.CALTABLE_DIR,
            temp_dir=temp_dir,
            sleep_interval=config.SLEEP_INTERVAL,
            station_name=config.STATION_NAME,
            integration_time_s=config.INTEGRATION_TIME_S,
            rcu_mode=config.RCU_MODE,
            height=height,
            extent=extent,
            pixels_per_metre=pixels_per_metre,
            step=step,
            max_threads=max_threads
        )

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
