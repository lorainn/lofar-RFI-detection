import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lofarimaging.rfi_tools import read_acm_real_time, generate_movie_from_list


# Configuration
if len(sys.argv) != 2:
    print("Usage: python realtime_movie_generation.py <input_path>")
    sys.exit(1)
input_path = sys.argv[1]
output_path = input_path + "/RFI-realtime-observation/"
caltable_dir = "CalTables/"
temp_dir = output_path + "temp"
fps = 10
sleep_interval = 0.2

# Observation info
station_name = "LV614"
integration_time_s = 2
rcu_mode = 3
height = 1.5

# Main loop
# Check if image list files already exist
sky_image_list_path = f"{temp_dir}/sky_image_list_realtime.txt"
nf_image_list_path = f"{temp_dir}/nf_image_list_realtime.txt"

skip_processing = False
if os.path.exists(sky_image_list_path) or os.path.exists(nf_image_list_path):
    user_input = input("Image list files already exist. Do you want to skip processing? (y/N): ").strip().lower()
    skip_processing = user_input == 'y'

if not skip_processing:
    read_acm_real_time(input_path, output_path, caltable_dir, temp_dir, sleep_interval, station_name, integration_time_s, rcu_mode, height)

generate_movie_from_list(f"{temp_dir}/sky_image_list_realtime.txt", f"{output_path}/sky_movie_realtime.mp4", fps=fps)
generate_movie_from_list(f"{temp_dir}/nf_image_list_realtime.txt", f"{output_path}/nf_movie_realtime.mp4", fps=fps)
print("Movie generation complete.")
