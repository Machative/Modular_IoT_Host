from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDateEdit, QDialog, QToolBar, QComboBox, QStackedWidget, 
    QTabWidget, QPushButton, QTextEdit, QListWidgetItem, QListWidget,
    QLineEdit
)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QAction, QActionGroup
from device import Device
from device import STATUS_CONN, STATUS_NO_CONN, MODE_CAPT, MODE_IDLE
import time

class PreferencesWindow(QDialog):
    def __init__(self, client, devices):
        super().__init__()
        self.setWindowTitle("Preferences")
        self.resize(500, 300)

        tabs = QTabWidget()

        # Tab 1: Devices
        tab1 = QWidget()
        tab1_layout = QVBoxLayout()
        self.ping_button = QPushButton("Find Devices")
        self.ping_button.clicked.connect(lambda: self.refreshDevList(client, devices))
        tab1_layout.addWidget(self.ping_button)
        
        self.device_list = QListWidget()
        self.refreshDevList(client, devices)

        tab1_layout.addWidget(self.device_list)
        
        tab1.setLayout(tab1_layout)

        # Tab 2: Placeholder
        tab2 = QWidget()
        tab2_layout = QVBoxLayout()
        tab2_layout.addWidget(QLabel("Options tab placeholder."))
        tab2.setLayout(tab2_layout)

        # Tab 3: Placeholder
        tab3 = QWidget()
        tab3_layout = QVBoxLayout()
        tab3_layout.addWidget(QLabel("This program was developed by Aidan Ferry."))
        tab3.setLayout(tab3_layout)

        tabs.addTab(tab1, "Devices")
        tabs.addTab(tab2, "Options")
        tabs.addTab(tab3, "About")

        layout = QVBoxLayout()
        layout.addWidget(tabs)
        self.setLayout(layout)

    def showDevice(self, device):
        item = QListWidgetItem(self.device_list)

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0,0,0,0)

        devID = QLabel(device.getUUID())

        devName = QLineEdit(device.getName())
        devName.editingFinished.connect(lambda: device.setName(devName.text()))

        button = QPushButton("Identify")
        button.clicked.connect(device.selfIdentify)

        row_layout.addWidget(devID)
        row_layout.addWidget(devName)
        row_layout.addStretch()
        row_layout.addWidget(button)

        item.setSizeHint(row_widget.sizeHint())
        self.device_list.setItemWidget(item,row_widget)

    def refreshDevList(self,client,devices):
        Device.find_devices(client,devices)
        self.device_list.clear()

        # Show connected devices in QListWidget
        for dev in devices:
            if dev.getStatus()==STATUS_CONN:
                self.showDevice(dev)
        if self.device_list.count()==0:
            item = QListWidgetItem("No devices found.")
            self.device_list.addItem(item)