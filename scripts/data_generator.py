import time
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lofarimaging import get_station_type, rcus_in_station
import config

def simulate_data_stream():
    input_path = config.SIMULATED_DAT_PATH
    output_path = config.SIMULATED_OUTPUT_PATH
    station_name = config.STATION_NAME
    interval_sec = 1.0  # One block per second

    station_type = get_station_type(station_name)
    num_rcu = rcus_in_station(station_type)
    block_size = num_rcu * num_rcu

    print(f"Simulating from '{input_path}' to '{output_path}'")
    print(f"Station: {station_name} | Block size: {block_size} complex128 | Interval: {interval_sec}s")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write the observation metadata file
    metadata_path = os.path.join(os.path.dirname(output_path), "metadata.h")
    with open(metadata_path, "w") as meta_file:
        meta_file.write(f"subbands={config.SIMULATED_SUBBAND_MIN}:{config.SIMULATED_SUBBAND_MAX}\n")
    print(f"Metadata written to: {metadata_path}")

    # Calculate total number of blocks based on file size
    input_file_size = os.path.getsize(input_path)
    block_bytes = block_size * 16  # complex128 = 16 bytes
    total_blocks = input_file_size // block_bytes

    print(f"Input file size: {input_file_size / (1024**2):.2f} MB")
    print(f"Estimated total blocks: {total_blocks}")

    # Create or truncate output file
    try:
        with open(output_path, "wb") as f_out, open(input_path, "rb") as f_in:
            block_counter = 0

            while True:
                block_data = f_in.read(block_bytes)
                if not block_data or len(block_data) < block_bytes:
                    print("End of input file or incomplete block.")
                    break

                f_out.write(block_data)
                f_out.flush()
                block_counter += 1
                print(f"[{block_counter}/{total_blocks}] Block written.")
                time.sleep(interval_sec)

        print("Simulation complete.")

    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")

        try:
            answer = input("Do you want to delete the generated files? [y/N]: ").strip().lower()
            if answer == "y":
                os.remove(output_path)
                print(f"Removed file: {output_path}")
                os.remove(metadata_path)
                print(f"Removed file: {metadata_path}")
        except Exception as e:
            print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    simulate_data_stream()
