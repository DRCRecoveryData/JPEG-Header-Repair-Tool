# JPEG Header Repair Tool

![Python Version](https://img.shields.io/badge/python-3.12.3%2B-blue)
![License](https://img.shields.io/github/license/DRCRecoveryData/JPEG-Header-Repair-Tool)

## Overview

This Python script facilitates the repair of corrupted JPEG file headers, specifically targeting issues with essential markers like the Start of Image (SOI) marker. JPEG files can become corrupted due to various reasons, including incomplete downloads, file system errors, or improper handling during transfer.

### Features

- **Header Reconstruction:** Automatically repairs missing or corrupted SOI markers and other essential headers based on a reference JPEG file.
- **Error Handling:** Detects and reports common issues such as missing markers, invalid marker placements, or malformed headers.
- **EXIF Data Removal:** Removes EXIF data to fix certain types of corruption.
- **Batch Processing:** Supports batch processing of multiple JPEG files within a specified directory for efficient repair operations.
- **Detailed Error Reporting:** Provides detailed error messages and logs to aid in diagnosing JPEG file corruption and repair outcomes.

## Usage

### Prerequisites

- Python 3.9 or higher installed on your system.

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/jpeg-header-repair-tool.git
    cd jpeg-header-repair-tool
    ```

### How to Run

1. Navigate to the directory where the script `jpegheaderrepair.py` is located.

2. Run the script with Python:
    ```bash
    python jpegheaderrepair.py
    ```

3. Follow the prompts to input paths to the reference JPEG file and the folder containing corrupted JPEG files.

4. Review the repaired JPEG files saved in the specified output directory (`Repaired/` by default) and check the error logs for detailed repair outcomes.

### Example

```bash
python jpegheaderrepair.py
Enter the path to the reference JPEG file: path/to/reference.jpg
Enter the path to the folder containing corrupted JPEG files: path/to/corrupted_folder
```

### Contributing

Contributions and feedback are welcome! If you encounter issues, have suggestions for improvements, or want to add features, feel free to fork the repository and submit a pull request.

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
