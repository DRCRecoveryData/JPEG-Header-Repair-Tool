import os
import math
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Global lock for synchronized printing
print_lock = threading.Lock()

def find_last_ffda_segment(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()
        last_ffda_index = data.rfind(b'\xff\xda')
        if last_ffda_index == -1:
            raise ValueError(f"No FFDA marker found in {file_path}")
        return data[:last_ffda_index + 14]

def calculate_entropy(data):
    """Calculate the Shannon entropy of the data."""
    if not data:
        return 0

    byte_counts = Counter(data)
    total_bytes = len(data)
    entropy = 0

    for count in byte_counts.values():
        probability = count / total_bytes
        entropy -= probability * math.log2(probability)

    return entropy

def repair_jpeg(reference_segment, corrupted_path, output_dir):
    # Read the corrupted JPEG file
    try:
        with open(corrupted_path, 'rb') as file:
            corrupted_data = file.read()
    except IOError as e:
        with print_lock:
            print(f"File access error with {corrupted_path}: {e}")
        return

    if len(corrupted_data) == 0:
        with print_lock:
            print(f"File size error: {corrupted_path} is 0 bytes. Cannot be repaired.")
        return

    # Find the last FFDA segment + 12 bytes in the corrupted JPEG file
    last_ffda_index_corrupted = corrupted_data.rfind(b'\xff\xda')
    if last_ffda_index_corrupted == -1:
        with print_lock:
            print(f"No JPEG SOI: No FFDA marker found in {corrupted_path}.")
        return

    # Data after the last FFDA + 12 bytes in the corrupted JPEG file
    corrupted_tail = corrupted_data[last_ffda_index_corrupted + 14:]

    # Create repaired data by combining the reference segment and corrupted tail
    repaired_data = reference_segment + corrupted_tail

    # Save the repaired JPEG to the output directory
    corrupted_filename = os.path.basename(corrupted_path)
    repaired_path = os.path.join(output_dir, corrupted_filename)
    try:
        with open(repaired_path, 'wb') as repaired_file:
            repaired_file.write(repaired_data)
        with print_lock:
            print(f"Repaired file saved to: {repaired_path}")
            entropy = calculate_entropy(repaired_data)
            print(f"Entropy of repaired file: {entropy:.2f}")
            print("\nList of errors:")
            if len(corrupted_data) == 0:
                print(f"Filesize error: {corrupted_path} is 0 bytes. Cannot be repaired.")
            if entropy < 7.60:
                print("Entropy too low: File does not contain sufficient JPEG data. Possibly repairable with a reference file.")
            if entropy > 7.99:
                print("Entropy too high: File is likely encrypted. JPEG repair cannot decrypt encrypted files.")
            if last_ffda_index_corrupted == -1:
                print("No JPEG SOI: SOI (Start of Image) marker (FF D8) not detected. The file may not have a valid JPEG header.")
            if b"Error while parsing" in repaired_data:
                print("Error while parsing: Error occurred during parsing. This usually indicates severe corruption.")
            if b"Invalid Markers" in repaired_data:
                print("Invalid Markers: Invalid JPEG markers detected. Typically indicates widespread corruption.")
            if b"Render Error" in repaired_data:
                print("Render Error: Error occurred during rendering due to corruption in JPEG bitstream.")
    except IOError as e:
        with print_lock:
            print(f"File save error: Cannot save repaired file to {repaired_path}: {e}")

def process_folder(reference_jpeg, corrupted_folder, output_directory):
    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Load the reference segment once to avoid repeated I/O operations
    try:
        reference_segment = find_last_ffda_segment(reference_jpeg)
    except ValueError as e:
        with print_lock:
            print(f"Error with reference file {reference_jpeg}: {e}")
        return

    corrupted_files = [f for f in os.listdir(corrupted_folder) if f.lower().endswith(('.jpg', '.jpeg'))]
    
    # Use a ThreadPoolExecutor to process files in parallel
    with ThreadPoolExecutor() as executor:
        futures = []
        for corrupted_file in corrupted_files:
            corrupted_path = os.path.join(corrupted_folder, corrupted_file)
            futures.append(executor.submit(repair_jpeg, reference_segment, corrupted_path, output_directory))

        # Wait for all tasks to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                with print_lock:
                    print(f"Error during repair: {e}")

if __name__ == "__main__":
    # Prompt the user for the paths
    reference_jpeg = input("Enter the path to the reference JPEG file: ")
    corrupted_folder = input("Enter the path to the folder containing corrupted JPEG files: ")
    output_directory = "Repaired"

    # Process all corrupted JPEG files in the folder
    process_folder(reference_jpeg, corrupted_folder, output_directory)
