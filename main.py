import sys
import csv
from PySide6.QtWidgets import (QApplication, QMainWindow, 
QStackedWidget, QToolBar
)
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtCore import QDate, Qt

import paho.mqtt.client as mqtt
from plot import PlotPanel
from live import LivePanel
from capture import CapturePanel
from device import Device
from preferences import PreferencesWindow

class MainWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self.setWindowTitle("Main Window")
        self.resize(900, 700)

        devices = Device.importDevices(client)
        Device.find_devices(client,devices)

        # --- Central stacked widget (pages for Plot / Live) ---
        self.stacked = QStackedWidget()

        self.capture_panel = CapturePanel(client, devices)
        self.plot_panel = PlotPanel(devices)
        self.live_panel = LivePanel(client, devices)

        self.stacked.addWidget(self.capture_panel)
        self.stacked.addWidget(self.plot_panel)
        self.stacked.addWidget(self.live_panel)
        self.setCentralWidget(self.stacked)

        # --- Toolbar ---
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # Group for exclusive tab actions
        tab_group = QActionGroup(self)
        tab_group.setExclusive(True)

        # Capture tab action
        capture_action = QAction("Capture",self,checkable=True,checked=True)
        capture_action.triggered.connect(lambda: self.stacked.setCurrentIndex(0))
        toolbar.addAction(capture_action)
        tab_group.addAction(capture_action)

        # Plot tab action
        plot_action = QAction("Plot", self, checkable=True)
        plot_action.triggered.connect(lambda: self.stacked.setCurrentIndex(1))
        toolbar.addAction(plot_action)
        tab_group.addAction(plot_action)

        # Live tab action
        live_action = QAction("Live", self, checkable=True)
        live_action.triggered.connect(lambda: self.stacked.setCurrentIndex(2))
        toolbar.addAction(live_action)
        tab_group.addAction(live_action)

        toolbar.addSeparator()

        # Settings button aligned to the right
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(lambda: self.open_preferences(client, devices))
        toolbar.addAction(settings_action)
        
        toolbar.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    def open_preferences(self, client, devices):
        dialog = PreferencesWindow(client, devices)
        dialog.exec()
        self.updateDevices(devices)

    def updateDevices(self,devices):
        self.capture_panel.updateDevices(devices)
        self.plot_panel.updateDevices(devices)
        self.live_panel.updateDevices(devices)

def on_connect(client,userdata,flags,reason_code,properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}.")
    else: 
        pass

if __name__ == "__main__":
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.connect_async("datalog.local",1883)
    mqtt_client.on_connect = on_connect;
    mqtt_client.loop_start()

    app = QApplication(sys.argv)
    window = MainWindow(mqtt_client)
    window.show()

    sys.exit(app.exec())
    mqtt_client.loop_stop()
    mqtt_client.disconnect()