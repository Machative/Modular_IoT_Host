import numpy as np
import matplotlib.pyplot as plt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDateEdit, QDialog, QToolBar, QComboBox, QStackedWidget, 
    QTabWidget, QPushButton, QTextEdit
)
from PySide6.QtCore import QDate, Qt
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
        self.date1 = QDateEdit()
        self.date1.setCalendarPopup(True)
        self.date1.setDate(QDate.currentDate())

        label2 = QLabel("End Date:")
        self.date2 = QDateEdit()
        self.date2.setCalendarPopup(True)
        self.date2.setDate(QDate.currentDate())

        date_layout.addWidget(label1)
        date_layout.addWidget(self.date1)
        date_layout.addSpacing(20)
        date_layout.addWidget(label2)
        date_layout.addWidget(self.date2)

        # Graph
        x_data = np.linspace(0, 10, 100)
        y_data = np.sin(x_data)

        fig, ax = plt.subplots()
        ax.plot(x_data, y_data, label="Sample Data")
        ax.set_xlabel("X Axis")
        ax.set_ylabel("Y Axis")
        ax.legend()

        self.canvas = FigureCanvas(fig)

        # Assemble Layout
        layout.addLayout(top_row)
        layout.addLayout(date_layout)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def deviceSelected(self, devices):
        for dev in devices:
            if dev.getName() == self.device_dropdown.currentText():
                self.currentDev = dev

    def updateDevices(self,devices):
        self.device_dropdown.clear()
        self.device_dropdown.addItems(dev.getName() for dev in devices)