import numpy as np
import time
import matplotlib.pyplot as plt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDateEdit, QDialog, QToolBar, QComboBox, QStackedWidget, 
    QTabWidget, QPushButton, QTextEdit
)
from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class LivePanel(QWidget):
    def __init__(self, client, devices):
        super().__init__()
        layout = QVBoxLayout()

        self.historySec = 5 #seconds of most recent data to display at once
        self.buffer = []

        self.currentDev = None
        if devices:
            self.currentDev = devices[0]

        # Row 1: Device label + dropdown
        device_row = QHBoxLayout()
        device_label = QLabel("Device:")
        self.device_dropdown = QComboBox()
        self.device_dropdown.addItems(dev.getName() for dev in devices)
        self.device_dropdown.currentIndexChanged.connect(lambda: self.deviceSelected(client, devices))
        device_row.addWidget(device_label)
        device_row.addWidget(self.device_dropdown)

        # Row 2: Graph (sample data for now)
        self.x_live = []
        self.y_live = []

        fig, self.ax = plt.subplots()
        (self.line,) = self.ax.plot([],[])
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        #self.ax.legend()

        self.live_canvas = FigureCanvas(fig)

        # Assemble Live page
        layout.addLayout(device_row)
        layout.addWidget(self.live_canvas)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updatePlot)
    
    def newData(self,client,userdata,msg):
        data = msg.payload.decode()
        self.buffer.append([time.time_ns()/1000000,float(data)])

    def deviceSelected(self, client, devices):
        self.timer.stop()
        for dev in devices:
            if dev.getName() == self.device_dropdown.currentText():
                self.currentDev = dev
                self.timer.start(500/self.currentDev.getSampleRate()) #Refresh plot at 2x sample rate of device

                curData = self.currentDev.getUUID()+"/data"
                client.subscribe(curData)
                client.message_callback_add(curData, self.newData)

    def updatePlot(self):
        while self.buffer:
            fo = self.buffer.pop(0)
            self.x_live.append(fo[0])
            self.y_live.append(fo[1])

        # Keep only last historyLen points (scrolling window)
        #TODO: Something is going wrong here when the sample rate gets changed
        historyLen = int(self.currentDev.getSampleRate() * self.historySec)
        self.x_live = self.x_live[-historyLen:]
        self.y_live = self.y_live[-historyLen:]

        # Update the line data
        self.line.set_xdata(self.x_live)
        self.line.set_ydata(self.y_live)

        # Adjust axis limits
        self.ax.relim()
        self.ax.autoscale_view()

        # Refresh the canvas
        self.live_canvas.draw_idle()
            
    def updateDevices(self,devices):
        self.device_dropdown.clear()
        self.device_dropdown.addItems(dev.getName() for dev in devices)