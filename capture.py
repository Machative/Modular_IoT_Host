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

from device import STATUS_CONN, STATUS_NO_CONN, STATUS_CAPT

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
        desc_label = QLabel("Description:")
        self.desc_box = QTextEdit()
        fm = QFontMetrics(self.desc_box.font())
        line_height = fm.lineSpacing()
        self.desc_box.setFixedHeight(line_height * 3 + 10)
        layout.addWidget(desc_label)
        layout.addWidget(self.desc_box)

        # Row 3: Units
        units_row = QHBoxLayout()
        units_label = QLabel("Units:")
        self.units_box = QLineEdit()
        units_row.addWidget(units_label)
        units_row.addWidget(self.units_box)
        layout.addLayout(units_row)

        # Row 4: Sample Rate
        rate_row = QHBoxLayout()
        rate_label = QLabel("Sample Rate:")
        self.rate_box = QLineEdit()
        rate_row.addWidget(rate_label)
        rate_row.addWidget(self.rate_box)
        layout.addLayout(rate_row)

        # Row 5: Capture button + Status
        capture_row = QHBoxLayout()
        self.capture_button = QPushButton("Capture")
        self.capture_button.clicked.connect(lambda: self.captureToggle(self.currentDev))
        self.status_label = QLabel("")
        capture_row.addWidget(self.capture_button)
        capture_row.addWidget(self.status_label)
        layout.addLayout(capture_row)

        # Finalize layout
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
    echo "$(date + '%Y-%m-%d %H:%M:%S'),$line" >> {fileout}
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
StandardError=jounral

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
            if device.getStatus()==STATUS_CONN: #Begin capture
                if os.path.exists("/etc/systemd/system/"+servicename):
                    subprocess.run(["sudo","systemctl","enable",servicename],check=True)
                    subprocess.run(["sudo","systemctl","start",servicename],check=True)
                else:
                    self.createMQTTLogger(device)
                device.setStatus(STATUS_CAPT)
            elif device.getStatus()==STATUS_CAPT: #Stop capture
                subprocess.run(["sudo","systemctl","stop",servicename],check=True)
                subprocess.run(["sudo","systemctl","disable",servicename],check=True)
                device.setStatus(STATUS_CONN)
            else: 
                #TODO: Device disconnected, remove
                pass
            self.status_label = device.getStatus()

    def deviceSelected(self, devices):
        for dev in devices:
            if dev.getName() == self.device_dropdown.currentText():
                self.currentDev = dev
                self.status_label.setText(self.currentDev.getStatus())

    def updateDevices(self, devices):
        self.device_dropdown.clear()
        self.device_dropdown.addItems(dev.getName() for dev in devices)
