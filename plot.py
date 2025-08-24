import numpy as np
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDateTimeEdit, QDialog, QToolBar, QComboBox, QStackedWidget, 
    QTabWidget, QPushButton, QTextEdit
)
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QAction, QActionGroup
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class PlotPanel(QWidget):
    def __init__(self, devices):
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

        # Row 2: Date selectors
        date_layout = QHBoxLayout()
        label1 = QLabel("Start Date:")
        self.date1 = QDateTimeEdit()
        self.date1.setCalendarPopup(True)
        self.date1.setDisplayFormat("MM/dd/yyyy hh:mm AP")
        self.date1.dateTimeChanged.connect(self.updatePlot)

        label2 = QLabel("End Date:")
        self.date2 = QDateTimeEdit()
        self.date2.setCalendarPopup(True)
        self.date2.setDisplayFormat("MM/dd/yyyy hh:mm AP")
        self.date2.dateTimeChanged.connect(self.updatePlot)

        date_layout.addWidget(label1)
        date_layout.addWidget(self.date1)
        date_layout.addSpacing(20)
        date_layout.addWidget(label2)
        date_layout.addWidget(self.date2)

        # Graph
        self.x_data = []
        self.y_data = []

        fig, self.ax = plt.subplots()
        (self.line,) = self.ax.plot([],[])
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")

        self.canvas = FigureCanvas(fig)

        self.date1.setDateTime(QDateTime.currentDateTime().addSecs(60 * -10))
        self.date2.setDateTime(QDateTime.currentDateTime())

        # Assemble Layout
        layout.addLayout(top_row)
        layout.addLayout(date_layout)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def readSelectedData(self):
        self.x_data.clear()
        self.y_data.clear()
        
        fromDate = self.date1.dateTime().toString("yyyy-MM-dd_HH:mm")
        toDate = self.date2.dateTime().toString("yyyy-MM-dd_HH:mm")
        if self.currentDev:
            devData = "res/"+self.currentDev.getUUID()+"_log.csv"
            with open(devData) as fp:
                reader = csv.reader(fp, delimiter=",",quotechar='"')
                for row in reader:
                    timestamp, frac = row[0].split(".")
                    if timestamp >= fromDate and timestamp <= toDate:
                        dt = datetime.strptime(timestamp,"%Y-%m-%d_%H:%M:%S")
                        us = int(frac)*10_000
                        dt = dt.replace(microsecond=us)
                        epochTime = dt.timestamp()
                        self.x_data.append(epochTime)
                        self.y_data.append(float(row[1]))


    def updatePlot(self):
        self.readSelectedData()

        # Update the line data
        self.line.set_xdata(self.x_data)
        self.line.set_ydata(self.y_data)

        # Adjust axis limits
        self.ax.relim()
        self.ax.autoscale_view()

        # Refresh the canvas
        self.canvas.draw_idle()

    def deviceSelected(self, devices):
        for dev in devices:
            if dev.getName() == self.device_dropdown.currentText():
                self.currentDev = dev

    def updateDevices(self,devices):
        self.device_dropdown.clear()
        self.device_dropdown.addItems(dev.getName() for dev in devices)