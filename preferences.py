from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDateEdit, QDialog, QToolBar, QComboBox, QStackedWidget, 
    QTabWidget, QPushButton, QTextEdit, QListWidgetItem, QListWidget,
    QLineEdit
)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QAction, QActionGroup
from device import Device
from device import STATUS_CONN, STATUS_NO_CONN, STATUS_CAPT
import time

class PreferencesWindow(QDialog):
    def __init__(self, client, devices):
        super().__init__()
        self.setWindowTitle("Preferences")
        self.resize(500, 300)

        tabs = QTabWidget()

        client.message_callback_add("ping", self.on_message)
        self.ping_list = []
        self.ping_timeout = 1

        # Tab 1: Devices
        tab1 = QWidget()
        tab1_layout = QVBoxLayout()
        self.ping_button = QPushButton("Find Devices")
        self.ping_button.clicked.connect(lambda: self.find_devices(client, devices))
        tab1_layout.addWidget(self.ping_button)
        
        self.device_list = QListWidget()
        self.refreshDevList(devices, client)

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

    def addDevice(self, device):
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

    def refreshDevList(self, devices, client):
        self.device_list.clear()
        for devID in self.ping_list:
            newDev = Device(devID, client)
            newDev.setStatus(STATUS_CONN)
            devices.append(newDev)

        if devices:
            for dev in devices:
                self.addDevice(dev)
        else:
            item = QListWidgetItem("No devices found.")
            self.device_list.addItem(item)

    def on_message(self,client,userdata,msg):
        message = msg.payload.decode()
        if not message == "ping":
            self.ping_list.append(message)
                
    def find_devices(self, client, devices):
        devices.clear()
        self.ping_list = []

        client.subscribe("ping")
        client.publish("ping","ping")
        ping_start = time.time()
        #TODO: Make this threaded. See device.self_identify for example
        while(time.time() - ping_start <= self.ping_timeout): pass
        
        self.refreshDevList(devices, client)
        client.unsubscribe("ping")