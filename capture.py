import numpy as np
import os, subprocess
import matplotlib.pyplot as plt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDateEdit, QDialog, QToolBar, QComboBox, QStackedWidget, 
    QTabWidget, QPushButton, QTextEdit, QLineEdit
)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QAction, QActionGroup, QFontMetrics
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from pathlib import Path

from device import STATUS_CONN, STATUS_NO_CONN, MODE_CAPT, MODE_IDLE

class CapturePanel(QWidget):
    def __init__(self, client, devices):
        super().__init__()
        layout = QVBoxLayout()

        self.currentDev = None
        if devices:
            self.currentDev = devices[0]

        # Row 1: Label + dropdown
        top_row = QHBoxLayout()
        label = QLabel("Device:")
        self.device_dropdown = QComboBox()
        self.device_dropdown.addItems(dev.getName() for dev in devices)
        self.device_dropdown.currentIndexChanged.connect(lambda: self.deviceSelected(devices))
        top_row.addWidget(label)
        top_row.addWidget(self.device_dropdown)
        layout.addLayout(top_row)

        # Row 2: Description
        desc_row = QHBoxLayout()
        desc_label = QLabel("Description:")
        self.desc_box = QLineEdit()
        self.desc_box.editingFinished.connect(lambda: self.currentDev.setDesc(self.desc_box.text()))
        desc_row.addWidget(desc_label)
        desc_row.addWidget(self.desc_box)
        layout.addLayout(desc_row)

        # Row 3: Units
        units_row = QHBoxLayout()
        units_label = QLabel("Units:")
        self.units_box = QLineEdit()
        self.units_box.editingFinished.connect(lambda: self.currentDev.setUnits(self.units_box.text()))
        units_row.addWidget(units_label)
        units_row.addWidget(self.units_box)
        layout.addLayout(units_row)

        # Row 4: Sample Rate
        rate_row = QHBoxLayout()
        rate_label = QLabel("Sample Rate:")
        self.rate_box = QLineEdit()
        self.rate_box.editingFinished.connect(lambda: self.currentDev.setSampleRate(self.rate_box.text()))
        rate_row.addWidget(rate_label)
        rate_row.addWidget(self.rate_box)
        layout.addLayout(rate_row)

        # Row 5: Capture button | Mode | Status
        capture_row = QHBoxLayout()
        self.capture_button = QPushButton("Capture")
        self.capture_button.clicked.connect(lambda: self.captureToggle(self.currentDev))
        self.mode_label = QLabel("")
        self.status_label = QLabel("")
        capture_row.addWidget(self.capture_button)
        capture_row.addWidget(self.mode_label)
        capture_row.addWidget(self.status_label)
        layout.addLayout(capture_row)

        # Finalize layout
        if devices: self.deviceSelected(devices) # Populate fields with details for defaultly selected device
        layout.addStretch()
        self.setLayout(layout)

    def createMQTTLogger(self,device):
        uuid = device.getUUID()
        topic = uuid+"/data"
        root = os.path.dirname(os.path.realpath(__file__))
        fileout = root+"/res/"+uuid+"_log.csv"

        bash_code = f"""#!/bin/bash
mosquitto_sub -h datalog.local -p 1883 -t "{topic}" | while read -r line
do
    echo "$(date +'%Y-%m-%d_%H:%M:%S.%2N'),$line" >> {fileout}
done
"""

        bashfile = root+"/scripts/"+uuid+"_log.sh"
        Path(bashfile).write_text(bash_code)
        os.chmod(bashfile, 0o755)

        service_code = f"""[Unit]
Description=MQTT Logger Service for {uuid}
After=network.target

[Service]
ExecStart={bashfile}
Restart=always
User={os.getenv("USER")}
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

        servicename = uuid+"_log.service"
        tempfile = root+"/"+servicename
        Path(tempfile).write_text(service_code)
        subprocess.run(["sudo","mv",tempfile,"/etc/systemd/system/"])
        
        try:
            subprocess.run(["sudo","systemctl","daemon-reload"],check=True)
            subprocess.run(["sudo","systemctl","enable",servicename],check=True)
            subprocess.run(["sudo","systemctl","start",servicename],check=True)
        except subprocess.CalledProcessError as e:
            print("Could not enable or start logging service.")

    def captureToggle(self, device):
        if device:
            servicename = device.getUUID()+"_log.service"
            if device.getMode()==MODE_IDLE: #Begin capture
                if os.path.exists("/etc/systemd/system/"+servicename) and os.path.exists(os.path.dirname(os.path.realpath(__file__))+"/scripts/"+device.getUUID()+"_log.sh"):
                    subprocess.run(["sudo","systemctl","enable",servicename],check=True)
                    subprocess.run(["sudo","systemctl","start",servicename],check=True)
                else:
                    self.createMQTTLogger(device)
                device.setMode(MODE_CAPT)
                self.capture_button.setText("Stop capture")
            elif device.getMode()==MODE_CAPT: #Stop capture
                subprocess.run(["sudo","systemctl","stop",servicename],check=True)
                subprocess.run(["sudo","systemctl","disable",servicename],check=True)
                device.setMode(MODE_IDLE)
                self.capture_button.setText("Capture")
            self.mode_label.setText(device.getMode())

    def deviceSelected(self, devices):
        for dev in devices:
            if dev.getName() == self.device_dropdown.currentText():
                self.currentDev = dev
                self.mode_label.setText(self.currentDev.getMode())
                self.status_label.setText(self.currentDev.getStatus())
                self.desc_box.setText(self.currentDev.getDesc())
                self.units_box.setText(self.currentDev.getUnits())
                self.rate_box.setText(str(self.currentDev.getSampleRate()))

    def updateDevices(self, devices):
        self.device_dropdown.clear()
        self.device_dropdown.addItems(dev.getName() for dev in devices)
