import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QProgressBar, QTextEdit, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import threading

class JPEGHeaderTool(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("JPEG Header Tool")
        self.setGeometry(100, 100, 400, 400)

        layout = QVBoxLayout()

        self.reference_label = QLabel("Reference JPEG:")
        self.reference_path_edit = QLineEdit()
        self.reference_browse_button = QPushButton("Browse", self)
        self.reference_browse_button.setObjectName("browseButton")
        self.reference_browse_button.clicked.connect(self.browse_reference_jpeg)

        self.corrupted_label = QLabel("Corrupted Folder:")
        self.corrupted_path_edit = QLineEdit()
        self.corrupted_browse_button = QPushButton("Browse", self)
        self.corrupted_browse_button.setObjectName("browseButton")
        self.corrupted_browse_button.clicked.connect(self.browse_corrupted_folder)

        self.repair_button = QPushButton("Start Repair", self)
        self.repair_button.setObjectName("blueButton")
        self.repair_button.clicked.connect(self.start_repair)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        layout.addWidget(self.reference_label)
        layout.addWidget(self.reference_path_edit)
        layout.addWidget(self.reference_browse_button)
        layout.addWidget(self.corrupted_label)
        layout.addWidget(self.corrupted_path_edit)
        layout.addWidget(self.corrupted_browse_button)
        layout.addWidget(self.repair_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_box)

        self.setLayout(layout)

        self.setStyleSheet("""
        #browseButton, #blueButton {
            background-color: #3498db;
            border: none;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 4px;
        }
        #browseButton:hover, #blueButton:hover {
            background-color: #2980b9;
        }
        """)

    def browse_reference_jpeg(self):
        reference_jpeg = QFileDialog.getOpenFileName(self, "Select Reference JPEG")[0]
        if reference_jpeg:
            self.reference_path_edit.setText(reference_jpeg)

    def browse_corrupted_folder(self):
        corrupted_folder = QFileDialog.getExistingDirectory(self, "Select Corrupted JPEG Folder")
        if corrupted_folder:
            self.corrupted_path_edit.setText(corrupted_folder)

    def start_repair(self):
        reference_jpeg = self.reference_path_edit.text()
        corrupted_folder = self.corrupted_path_edit.text()

        if not os.path.isfile(reference_jpeg):
            self.show_message("Error", "Invalid reference JPEG file.")
            return

        if not os.path.isdir(corrupted_folder):
            self.show_message("Error", "Invalid corrupted JPEG folder.")
            return

        # Create the Repaired folder if it doesn't exist
        output_folder = "Repaired"
        os.makedirs(output_folder, exist_ok=True)

        # Create the repair worker and start the repair process
        self.worker = RepairWorker(reference_jpeg, corrupted_folder, output_folder)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_updated.connect(self.update_log)
        self.worker.repair_finished.connect(self.repair_finished)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, message):
        self.log_box.append(message)

    def repair_finished(self, message):
        self.show_message("Repair Complete", message)

    def show_message(self, title, message):
        QMessageBox.information(self, title, message)

class RepairWorker(QThread):
    progress_updated = pyqtSignal(int)
    log_updated = pyqtSignal(str)
    repair_finished = pyqtSignal(str)

    def __init__(self, reference_jpeg, corrupted_folder, output_folder):
        super().__init__()
        self.reference_jpeg = reference_jpeg
        self.corrupted_folder = corrupted_folder
        self.output_folder = output_folder

    def run(self):
        try:
            reference_segment = find_last_ffda_segment(self.reference_jpeg)
        except ValueError as e:
            self.log_updated.emit(f"Error with reference file {self.reference_jpeg}: {e}")
            return

        corrupted_files = [f for f in os.listdir(self.corrupted_folder) if f.lower().endswith(('.jpg', '.jpeg'))]
        total_files = len(corrupted_files)
        files_processed = 0
        progress_step = 100 / total_files

        for corrupted_file in corrupted_files:
            corrupted_path = os.path.join(self.corrupted_folder, corrupted_file)
            self.log_updated.emit(f"Repairing {corrupted_file}...")
            repair_result = repair_jpeg(reference_segment, corrupted_path, self.output_folder)
            self.log_updated.emit(repair_result)
            files_processed += 1
            progress = files_processed * progress_step
            self.progress_updated.emit(int(progress))

        self.repair_finished.emit("Repair process completed.")

def find_last_ffda_segment(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()
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
        return f"File access error with {corrupted_path}: {e}"

    if len(corrupted_data) == 0:
        return f"File size error: {corrupted_path} is 0 bytes. Cannot be repaired."

    # Find the last FFDA segment + 12 bytes in the corrupted JPEG file
    last_ffda_index_corrupted = corrupted_data.rfind(b'\xff\xda')
    if last_ffda_index_corrupted == -1:
        return f"No JPEG SOI: No FFDA marker found in {corrupted_path}."

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
        repair_log = f"Repaired file saved to: {repaired_path}\n"
        return repair_log
    except IOError as e:
        return f"File save error: Cannot save repaired file to {repaired_path}: {e}"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = JPEGHeaderTool()
    window.show()
    sys.exit(app.exec())
