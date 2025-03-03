import sys
import numpy as np
import pandas as pd
import threading
import time

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QSpinBox,
    QDoubleSpinBox, QComboBox, QProgressBar, QTabWidget, QHBoxLayout,
    QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from process_data import *

ICONS = 'icons'
COLORS = {
    'background': '#2E3440',
    'text': '#D8DEE9',
    'widget_background': '#4C566A',
    'border': '#81A1C1',
    'hover': '#5E81AC',
    'disabled_background': '#3B4252',
    'disabled_text': '#B0BEC5'
}

class DLSMeasurementApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DLS Measurement App")
        self.setGeometry(100, 100, 800, 600)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                font-size: 14px;
            }}
            QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox, QComboBox {{
                background-color: {COLORS['widget_background']};
                border: 1px solid {COLORS['border']};
                padding: 8px;
                border-radius: 8px;
                color: white;
            }}
            QPushButton:hover {{
                background-color: {COLORS['hover']};
            }}
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
            QTabWidget::tab-bar {{
                alignment: center;
            }}
            QTabBar::tab {{
                background: {COLORS['widget_background']};
                border: 1px solid {COLORS['border']};
                margin: 1px;
                padding: 6px;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['hover']};
            }}
            QGroupBox {{
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {COLORS['text']};
            }}
            QCheckBox::indicator:unchecked {{
                border: 2px solid {COLORS['border']};
                border-radius: 3px;
                background-color: {COLORS['widget_background']};
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {COLORS['border']};
                border-radius: 3px;
                background-color: {COLORS['border']};
            }}
            QComboBox:disabled,
            QDoubleSpinBox:disabled,
            QSpinBox:disabled {{
                background-color: {COLORS['disabled_background']}; 
                color: {COLORS['disabled_text']};          
                border: 1px solid {COLORS['hover']}; 
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                background: {COLORS['widget_background']};
                border: 1px solid {COLORS['border']};
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
            QComboBox::down-arrow {{
                image: url("{ICONS}/down-arrow.svg");
                width: 16px;
                height: 16px;
            }}
            QSpinBox::up-button,
            QDoubleSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                border-top-right-radius: 8px;
                background: {COLORS['widget_background']};
                border: 1px solid {COLORS['border']};
                width: 20px;
            }}
            QSpinBox::down-button,
            QDoubleSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                border-bottom-right-radius: 8px;
                background: {COLORS['widget_background']};
                border: 1px solid {COLORS['border']};
                width: 20px;
            }}
            QSpinBox::up-arrow,
            QDoubleSpinBox::up-arrow {{
                image: url("{ICONS}/up-arrow.svg");
                width: 8px;
                height: 8px;
            }}
            QSpinBox::down-arrow,
            QDoubleSpinBox::down-arrow {{
                image: url("{ICONS}/down-arrow.svg");
                width: 8px;
                height: 8px;
            }}
        """)

        # Initialize user input values
        self.viscosity = 1.0
        self.meas_time = 30
        self.meas_interval = 5
        self.pump1_speed = 1.0
        self.pump2_speed = 1.0

        # Initialize measurement time
        self.measurement_time = 0

        # Data arrays for each sub-tab
        self.particle_time = []
        self.particle_size = []

        self.temp_time = []
        self.temp_values = []

        self.dls_time = []
        self.dls_values = []

        # Default viscosities
        self.viscosity_values = {
            "Silica": 1.2,
            "Polystyrene": 0.9,
            "Titanium Dioxide": 1.5
        }

        main_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create the three primary tabs
        self.measurement_tab = QWidget()
        self.settings_tab = QWidget()
        self.about_tab = QWidget()

        # Add tabs to QTabWidget
        self.tab_widget.addTab(self.measurement_tab, "Measurements")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        self.tab_widget.addTab(self.about_tab, "About This Device")

        # Set up each primary tab
        self.setup_measurement_tab()  
        self.setup_settings_tab()
        self.setup_about_tab()

        self.setLayout(main_layout)

        # Internal data and timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)

        # Initialize the blank graphs so progress bar stays at 0
        self.setup_blank_graphs()

        # Stop event for data collection
        self.stop_event = threading.Event() 

    def setup_measurement_tab(self):
        """
        The Measurements tab now contains:
          - Start/Stop Buttons
          - Progress Bar
          - A secondary QTabWidget with three sub-tabs:
              1) Particle Size
              2) Temperature
              3) DLS Reading
        """
        layout = QVBoxLayout()

        # Buttons (Start/Stop)
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Measurement")
        self.start_button.clicked.connect(self.start_measurement)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Measurement")
        self.stop_button.clicked.connect(self.stop_measurement)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)

        # Horizontal layout for progress label + progress bar
        progress_line_layout = QHBoxLayout()
        self.progress_label = QLabel("Measurement Progress")
        self.progress_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        progress_line_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%   ")
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLORS['border']};
                background: {COLORS['widget_background']};
                border-radius: 8px;
                color: white;
                padding: 8px;
                text-align: right;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['hover']};
                border-radius: 6px;
            }}
        """)
        progress_line_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_line_layout)

        # Sub-tab widget for particle size, temperature and DLS reading graphs
        self.measurement_subtabs = QTabWidget()
        layout.addWidget(self.measurement_subtabs)
        self.measurement_subtabs.setObjectName("measurementSubTabs")
        self.measurement_subtabs.setStyleSheet("""
            QTabWidget#measurementSubTabs::tab-bar {
                alignment: left; 
            }
        """)
        self.measurement_subtabs.setTabPosition(QTabWidget.South)

        # ----------------
        # 1) Particle Size Tab
        # ----------------
        self.particle_tab = QWidget()
        p_layout = QVBoxLayout()

        self.particle_fig = Figure()
        self.particle_ax = self.particle_fig.add_subplot(111)
        self.particle_canvas = FigureCanvas(self.particle_fig)
        p_layout.addWidget(self.particle_canvas)

        self.particle_tab.setLayout(p_layout)
        self.measurement_subtabs.addTab(self.particle_tab, "Particle Size")

        # ----------------
        # 2) Temperature Tab
        # ----------------
        self.temp_tab = QWidget()
        t_layout = QVBoxLayout()

        self.temp_fig = Figure()
        self.temp_ax = self.temp_fig.add_subplot(111)
        self.temp_canvas = FigureCanvas(self.temp_fig)
        t_layout.addWidget(self.temp_canvas)

        self.temp_tab.setLayout(t_layout)
        self.measurement_subtabs.addTab(self.temp_tab, "Temperature")

        # ----------------
        # 3) DLS Reading Tab
        # ----------------
        self.dls_tab = QWidget()
        d_layout = QVBoxLayout()

        self.dls_fig = Figure()
        self.dls_ax = self.dls_fig.add_subplot(111)
        self.dls_canvas = FigureCanvas(self.dls_fig)
        d_layout.addWidget(self.dls_canvas)

        self.dls_tab.setLayout(d_layout)
        self.measurement_subtabs.addTab(self.dls_tab, "DLS Reading")

        self.measurement_tab.setLayout(layout)

    def setup_settings_tab(self):
        """
        Sets up the UI on the second tab (Settings) with three sections:
          1) Viscosity
          2) Measurement Timing
          3) Pump Speed
        """
        main_layout = QVBoxLayout()

        # --------------------- Section 1: Viscosity ---------------------
        viscosity_group = QGroupBox("Viscosity")
        viscosity_layout = QVBoxLayout()

        self.manual_viscosity_checkbox = QCheckBox("  Manual Viscosity Entry")
        # default is unchecked => "Particle-based" mode
        self.manual_viscosity_checkbox.setChecked(False)
        self.manual_viscosity_checkbox.toggled.connect(self.toggle_viscosity_mode)
        viscosity_layout.addWidget(self.manual_viscosity_checkbox)

        # Particle Selection (only enabled if manual is NOT checked)
        self.particle_label = QLabel("Select Particle:")
        self.particle_selection = QComboBox()
        self.particle_selection.addItems(["Silica", "Polystyrene", "Titanium Dioxide"])
        self.particle_selection.currentTextChanged.connect(self.set_viscosity)
        viscosity_layout.addWidget(self.particle_label)
        viscosity_layout.addWidget(self.particle_selection)

        # Manual Viscosity (only enabled if manual is checked)
        self.viscosity_label = QLabel("Viscosity (mPa·s):")
        self.viscosity_input = QDoubleSpinBox()
        self.viscosity_input.setRange(0.1, 1000.0)
        self.viscosity_input.setValue(self.viscosity)
        self.viscosity_input.setEnabled(False)  # default -> disabled
        self.viscosity_input.valueChanged.connect(self.viscosity_input_changed)
        viscosity_layout.addWidget(self.viscosity_label)
        viscosity_layout.addWidget(self.viscosity_input)

        viscosity_group.setLayout(viscosity_layout)
        main_layout.addWidget(viscosity_group)

        # --------------------- Section 2: Measurement Timing ---------------------
        timing_group = QGroupBox("Measurement Timing")
        timing_layout = QVBoxLayout()

        self.time_label = QLabel("Total Measurement Time (s):")
        self.time_input = QSpinBox()
        self.time_input.setRange(1, 600)
        self.time_input.setValue(self.meas_time)
        self.time_input.valueChanged.connect(self.meas_time_input_changed)

        self.interval_label = QLabel("Measurement Interval (s):")
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 60)
        self.interval_input.setValue(self.meas_interval)
        self.interval_input.valueChanged.connect(self.meas_interval_input_changed)

        timing_layout.addWidget(self.time_label)
        timing_layout.addWidget(self.time_input)
        timing_layout.addWidget(self.interval_label)
        timing_layout.addWidget(self.interval_input)

        timing_group.setLayout(timing_layout)
        main_layout.addWidget(timing_group)

        # --------------------- Section 3: Pump Speed ---------------------
        pump_group = QGroupBox("Pump Speed")
        pump_layout = QVBoxLayout()

        self.pump_speed_label1 = QLabel("Pump Speed 1 (mL/min):")
        self.pump_speed_spin1 = QDoubleSpinBox()
        self.pump_speed_spin1.setRange(0.0, 1000.0)
        self.pump_speed_spin1.setValue(self.pump1_speed)
        self.pump_speed_spin1.valueChanged.connect(self.pump1_speed_input_changed)

        self.pump_speed_label2 = QLabel("Pump Speed 2 (mL/min):")
        self.pump_speed_spin2 = QDoubleSpinBox()
        self.pump_speed_spin2.setRange(0.0, 1000.0)
        self.pump_speed_spin2.setValue(self.pump2_speed)
        self.pump_speed_spin2.valueChanged.connect(self.pump2_speed_input_changed)

        pump_layout.addWidget(self.pump_speed_label1)
        pump_layout.addWidget(self.pump_speed_spin1)
        pump_layout.addWidget(self.pump_speed_label2)
        pump_layout.addWidget(self.pump_speed_spin2)

        pump_group.setLayout(pump_layout)
        main_layout.addWidget(pump_group)

        # Apply the overall layout to the Settings tab
        self.settings_tab.setLayout(main_layout)

    def setup_about_tab(self):
        """
        Sets up the UI on the third tab (About This Device).
        """
        layout = QVBoxLayout()

        about_label = QLabel("Make sure dingy fits in the pupu, snuggly...no wiggle")
        about_label.setStyleSheet("font-size: 20px;")
        about_label.setWordWrap(True)
        layout.addWidget(about_label)

        self.about_tab.setLayout(layout)

    def setup_blank_graphs(self):
        """
        Initialize empty/placeholder Matplotlib plots in all 3 sub-tabs
        so the progress bar stays at 0% until the user starts.
        """
        # Particle Size
        self.particle_ax.clear()
        self.particle_ax.set_title('Particle Size Over Time')
        self.particle_ax.set_xlabel('Time (s)')
        self.particle_ax.set_ylabel('Particle Size (nm)')
        self.particle_ax.grid()
        self.particle_canvas.draw()

        # Temperature
        self.temp_ax.clear()
        self.temp_ax.set_title('Temperature Over Time')
        self.temp_ax.set_xlabel('Time (s)')
        self.temp_ax.set_ylabel('Temperature (°C)')
        self.temp_ax.grid()
        self.temp_canvas.draw()

        # DLS Reading
        self.dls_ax.clear()
        self.dls_ax.set_title('DLS Reading Over Time')
        self.dls_ax.set_xlabel('Time (s)')
        self.dls_ax.set_ylabel('DLS Reading (a.u.)')
        self.dls_ax.grid()
        self.dls_canvas.draw()

    # ---------------------
    # Logic / Callbacks
    # ---------------------
    def toggle_viscosity_mode(self):
        """
        If checkbox is checked => Manual Viscosity
        If checkbox is unchecked => Particle-based Viscosity
        """
        if self.manual_viscosity_checkbox.isChecked():
            # Manual Viscosity => enable spinbox, disable particle selection
            self.viscosity_input.setEnabled(True)
            self.particle_selection.setEnabled(False)
        else:
            # Particle-based => disable spinbox, enable particle selection
            self.viscosity_input.setEnabled(False)
            self.particle_selection.setEnabled(True)
            self.set_viscosity()

    def set_viscosity(self):
        """Set the viscosity based on selected particle if in particle mode."""
        if not self.manual_viscosity_checkbox.isChecked():
            particle = self.particle_selection.currentText()
            default_viscosity = self.viscosity_values.get(particle, 1.0)
            self.viscosity_input.setValue(default_viscosity)
            self.viscosity = default_viscosity

    def viscosity_input_changed(self):
        """Change viscosity based on user input."""
        self.viscosity = self.viscosity_input.value()

    def meas_time_input_changed(self):
        """Change measurement time based on user input."""
        self.meas_time = self.time_input.value()

    def meas_interval_input_changed(self):
        """Change measurement interval based on user input."""
        self.meas_interval = self.interval_input.value()

    def pump1_speed_input_changed(self):
        """Change pump 1 speed based on user input."""
        self.pump1_speed = self.pump_speed_spin1.value()

    def pump2_speed_input_changed(self):
        """Change pump 2 speed based on user input."""
        self.pump2_speed = self.pump_speed_spin2.value()

    def csv_write_task(self):
        """Run CSV writing in a separate thread."""
        self.process_data.csv_write(duration=self.meas_time)
   
    def start_measurement(self):
        """Start the measurement timer and reset progress/data to 0."""
        self.measurement_time = 0

        self.particle_time.clear()
        self.particle_size.clear()

        self.temp_time.clear()
        self.temp_values.clear()

        self.dls_time.clear()
        self.dls_values.clear()

        self.progress_bar.setValue(0)

        # Start CSV writing in its own thread
        self.csv_writer = GetArdunioData()

        self.csv_thread = threading.Thread(target=self.csv_writer.csv_write, args=(self.meas_time,), daemon=True)
        self.csv_thread.start()

        time.sleep(2)

        interval_ms = self.meas_interval * 1000
        self.timer.start(interval_ms)


    def stop_measurement(self):
        """Stop the measurement timer."""
        self.timer.stop()

        # Stop CSV writing thread
        self.csv_writer.stop()

    def update_graph(self):
        """
        Update the three sub-tab graphs with simulated data
        and handle progress/time.
        """
        total_time = self.meas_time
        interval = self.meas_interval

        if self.measurement_time >= total_time:
            self.timer.stop()
            self.progress_bar.setValue(100)
            return

        self.measurement_time += interval

        progress_value = int((self.measurement_time / total_time) * 100)
        self.progress_bar.setValue(progress_value)

        # Simulate data for each sub-tab
        # 1) Particle size
        self.particle_time.append(self.measurement_time)
        self.particle_size.append(np.random.uniform(10, 500))  # random nm size

        # 2) Temperature
        self.temp_time.append(self.measurement_time)
        self.temp_values.append(np.random.uniform(20, 80))     # random °C

        # 3) DLS Reading
        self.dls_time.append(self.measurement_time)
        self.dls_values.append(np.random.uniform(0.1, 2.0))    # random DLS value

        df = pd.read_csv("data_output.csv")
        # -----------------------------
        # Update Particle Size Tab
        # -----------------------------
        self.particle_ax.clear()
        self.particle_ax.plot(
            self.particle_time,
            self.particle_size,
            label='Particle Size'
        )
        self.particle_ax.set_title('Particle Size Over Time')
        self.particle_ax.set_xlabel('Time (s)')
        self.particle_ax.set_ylabel('Size (nm)')
        self.particle_ax.grid()
        self.particle_canvas.draw()

        # -----------------------------
        # Update Temperature Tab
        # -----------------------------
        self.temp_ax.clear()
        self.temp_ax.plot(
            # self.temp_time,
            # self.temp_values,
            df['Time (seconds)'], df['Temperature'],
            color='orange',
            label='Temperature'
        )
        self.temp_ax.set_title('Temperature Over Time')
        self.temp_ax.set_xlabel('Time (s)')
        self.temp_ax.set_ylabel('Temperature (°C)')
        self.temp_ax.grid()
        self.temp_canvas.draw()

        # -----------------------------
        # Update DLS Reading Tab
        # -----------------------------
        self.dls_ax.clear()
        self.dls_ax.plot(
            # self.dls_time,
            # self.dls_values,
            df['Time (seconds)'], df['DLS Value'],
            color='green',
            label='DLS Reading'
        )
        self.dls_ax.set_title('DLS Reading Over Time')
        self.dls_ax.set_xlabel('Time (s)')
        self.dls_ax.set_ylabel('DLS Reading (a.u.)')
        self.dls_ax.grid()
        self.dls_canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DLSMeasurementApp()
    window.show()
    sys.exit(app.exec())
