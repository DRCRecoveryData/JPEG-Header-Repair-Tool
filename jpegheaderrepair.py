import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

def remove_exif(data):
    # JPEG markers that indicate the start of a segment
    marker_start = b'\xFF'
    app1_marker = b'\xFF\xE1'  # APP1 marker (where EXIF data is stored)
    
    i = 0
    while i < len(data) - 1:
        # Check if the current byte is a marker start
        if data[i] == 0xFF:
            marker = data[i:i+2]  # Get the marker (2 bytes)
            
            # If the marker is APP1 (EXIF data), remove the entire segment
            if marker == app1_marker:
                segment_length = int.from_bytes(data[i+2:i+4], byteorder='big') + 2
                data = data[:i] + data[i+segment_length:]  # Remove the segment
                continue  # Continue parsing from the current position
            
            # Skip other markers (except SOI and EOI)
            if marker not in (b'\xFF\xD8', b'\xFF\xD9'):  # Skip SOI and EOI
                segment_length = int.from_bytes(data[i+2:i+4], byteorder='big') + 2
                i += segment_length  # Move to the next segment
                continue
        
        i += 1  # Move to the next byte
    
    return data

def find_last_ffda_segment(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()
        data = remove_exif(data)  # Remove EXIF data from the reference file
        last_ffda_index = data.rfind(b'\xff\xda')
        if last_ffda_index == -1:
            raise ValueError(f"No FFDA marker found in {file_path}")
        return data[:last_ffda_index + 14]

def repair_jpeg(reference_segment, corrupted_path, output_dir):
    # Read the corrupted JPEG file
    try:
        with open(corrupted_path, 'rb') as file:
            corrupted_data = file.read()
    except IOError as e:
        print(f"File access error with {corrupted_path}: {e}")
        return

    if len(corrupted_data) == 0:
        print(f"File size error: {corrupted_path} is 0 bytes. Cannot be repaired.")
        return

    # Find the last FFDA segment + 12 bytes in the corrupted JPEG file
    last_ffda_index_corrupted = corrupted_data.rfind(b'\xff\xda')
    if last_ffda_index_corrupted == -1:
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
        print(f"Repaired file saved to: {repaired_path}")
    except IOError as e:
        print(f"File save error: Cannot save repaired file to {repaired_path}: {e}")

def process_folder(reference_jpeg, corrupted_folder, output_directory):
    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Load the reference segment once to avoid repeated I/O operations
    try:
        reference_segment = find_last_ffda_segment(reference_jpeg)
    except ValueError as e:
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
                print(f"Error during repair: {e}")

if __name__ == "__main__":
    # Prompt the user for the paths
    reference_jpeg = input("Enter the path to the reference JPEG file: ")
    corrupted_folder = input("Enter the path to the folder containing corrupted JPEG files: ")
    output_directory = "Repaired"

    # Process all corrupted JPEG files in the folder
    process_folder(reference_jpeg, corrupted_folder, output_directory)
