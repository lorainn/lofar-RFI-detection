# lofarimaging/rfi_tools/realtime-legacy.py

import numpy as np
import pandas as pd
import time
import os
import datetime
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lofarimaging import get_station_type, rcus_in_station, make_xst_plots
from webapp import state

__all__ = [
    "read_acm_real_time",
]


def wait_for_dat_file(input_path, sleep_interval=0.2):
    print(f"Waiting for a .dat file in {input_path}...")
    while True:
        files = [f for f in os.listdir(input_path) if f.endswith("_xst.dat")]
        if files:
            return os.path.join(input_path, files[0])  # Return first .dat file found
        time.sleep(sleep_interval)


def read_acm_real_time(input_path, output_path, caltable_dir, temp_dir, sleep_interval, station_name, integration_time_s, rcu_mode, height):
    station_type = get_station_type(station_name)
    num_rcu = rcus_in_station(station_type)
    block_size = num_rcu * num_rcu

    filename = wait_for_dat_file(input_path)
    print(f"File {filename} detected. Starting real-time reading...")
    buffer = np.array([], dtype=np.complex128)  # Buffer to accumulate incomplete data

    # Get min and max subbands
    min_subband, max_subband = get_subbands(input_path)
    current_subband = min_subband  # Start with the minimum subband

    # Initialize an empty DataFrame
    df = pd.DataFrame(columns=["timestamp", "subband", "dat_file", "h_file"])

    os.makedirs(temp_dir, exist_ok=True)
    sky_movie = []
    nf_movie = []

    fig, ax = plt.subplots(figsize=(10, 6))
    nf_img_display = None

    with open(filename, "rb") as f:
        while True:
            # Read new available data
            new_data = np.fromfile(f, dtype=np.complex128)

            # Accumulate data in the buffer
            buffer = np.concatenate((buffer, new_data))

            # Process full blocks if possible
            while buffer.size >= block_size:
                block = buffer[:block_size].reshape((num_rcu, num_rcu))

                # Save block to file
                obstime = datetime.datetime.now()
                timestamp = obstime.strftime('%Y%m%d_%H%M%S')  # Timestamp for filename
                output_filename = f"{output_path}{timestamp}_xst.dat"
                block.tofile(output_filename)  # Save block as .dat file
                print(f"Block saved as {output_filename}")

                # Block processing
                try:
                    print(temp_dir)
                    print(f"Generating image for subband {current_subband} at time {obstime} and height {height} m.")
                    sky_image_path, nf_image_path, _ = make_xst_plots(block, station_name, obstime, current_subband, rcu_mode, map_zoom=18, outputpath=temp_dir, mark_max_power=True, height=height, return_only_paths=True)
                    print(f"Image generated: {sky_image_path}, {nf_image_path}")
                    sky_movie.append(sky_image_path)
                    nf_movie.append(nf_image_path)
                except Exception as e:
                    print(f"Error generating image: {e}")

                # Export the image lists for movie generation
                try:
                    with open(f"{temp_dir}/sky_image_list_realtime.txt", "w") as sky_file:
                        sky_file.write("\n".join(sky_movie))

                    with open(f"{temp_dir}/nf_image_list_realtime.txt", "w") as nf_file:
                        nf_file.write("\n".join(nf_movie))
                except Exception as e:
                    print(f"Error writing image list files: {e}")

                h_file = None  # Placeholder for h_file

                # Add entry to DataFrame
                df = pd.concat([df, pd.DataFrame({
                    "timestamp": [timestamp],
                    "subband": [current_subband],
                    "dat_file": [output_filename],
                    "h_file": [h_file]
                })], ignore_index=True)

                # Update subband
                current_subband += 1
                if current_subband > max_subband:
                    current_subband = min_subband  # Reset to minimum subband

                # Remove processed data
                buffer = buffer[block_size:]

                # Show or update the image
                try:
                    print(temp_dir)
                    print(f"Generating image for subband {current_subband} at time {obstime} and height {height} m.")
                    sky_image_path, nf_image_path, _ = make_xst_plots(
                        block, station_name, obstime, current_subband, rcu_mode,
                        map_zoom=18, outputpath=temp_dir, mark_max_power=True,
                        height=height, return_only_paths=True
                    )
                    print(f"Image generated: {sky_image_path}, {nf_image_path}")

                    if sky_image_path is not None and nf_image_path is not None:
                        sky_movie.append(sky_image_path)
                        nf_movie.append(nf_image_path)

                        # Read image
                        img = mpimg.imread(nf_image_path)

                        # Send image to webapp
                        filename = os.path.basename(nf_image_path)
                        state.add_image_entry(filename, subband=current_subband)

                        # Show image
                        '''
                        if nf_img_display is None:
                            nf_img_display = ax.imshow(img)
                            ax.set_title(f"Near-field Image - Subband {current_subband}")
                            ax.axis('off')
                            plt.ion()  # Interactive mode on
                            plt.show()
                        else:
                            nf_img_display.set_data(img)
                            ax.set_title(f"Near-field Image - Subband {current_subband}")
                            fig.canvas.draw()
                            fig.canvas.flush_events()
                        '''
                    else:
                        print("One or both image paths are None; skipping append and display.")

                except Exception as e:
                    print(f"Error generating image: {e}")


            # If no new data, wait and retry
            if new_data.size == 0:
                time.sleep(sleep_interval)
                continue


def obs_parser(obs_file):
    obs_data = {'beams': []}
    with open(obs_file) as obs:
        lines = obs.readlines()
        for line in lines:
            if line.startswith('bits='):
                obs_data['bits'] = line.split('=')[1].replace('\n', '')

            elif line.startswith('rspctl --bitmode'):
                obs_data['bits'] = line.split('=')[1].replace('\n', '')

            elif line.startswith('- rspctl --bitmode'):
                obs_data['bits'] = line.split('=')[1].replace('\n', '')

            elif line.startswith('subbands='):
                obs_data['subbands'] = line.split('=')[1].replace('\n', '').replace("'", "")

            elif line.startswith("nohup beamctl "):
                beam_data = line.split()
                obs_data['beams'].append({'name': beam_data[7].split("=")[1].replace('$', '').lstrip('0,0,'),
                                          'beamlets': beam_data[6].split("=")[1]})

            elif line.startswith("$PREFIX beamctl"):
                beam_data = line.split()
                obs_data['beams'].append({'name': beam_data[7].split("=")[1].replace('$', '').lstrip('0,0,'),
                                          'beamlets': beam_data[6].split("=")[1]})

            elif line.startswith("- beamctl "):
                line = line.replace("- ", "")
                beam_data = line.split()
                #source_name = get_source_name(beam_data[7].split("=")[1].replace('$', ''))
                #obs_data['beams'].append({'name': source_name, 'beamlets': beam_data[4].split("=")[1]})
    return obs_data


def get_subbands(input_path):
    # Find the observation file in the input path
    time.sleep(0.5)
    obs_files = [f for f in os.listdir(input_path) if f.endswith(('.h', '.sh'))]
    if obs_files:
        obs_file = os.path.join(input_path, obs_files[0])  # Use the first matching file
    else:
        raise FileNotFoundError("No observation file (.h, .sh) found in the input path.")

    obs_data = obs_parser(obs_file)

    if 'subbands' in obs_data:
        # Convert subbands string to a list of integers
        subbands = list(map(int, obs_data['subbands'].split(':')))
        min_subband = min(subbands)
        max_subband = max(subbands)
        print(f"Min subband: {min_subband}, Max subband: {max_subband}")
    else:
        # Allow manual input for subbands if not found in the observation file
        print("No subbands information found in the observation file. Please input manually.")
        min_subband = int(input("Enter the minimum subband: "))
        max_subband = int(input("Enter the maximum subband: "))
        if min_subband >= max_subband or min_subband < 0 or max_subband < 0:
            raise ValueError("No subbands information found in the observation file.")

    return min_subband, max_subband
