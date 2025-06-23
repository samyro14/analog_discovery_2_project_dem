"""
Analog Discovery 2 Complete GUI Application
A comprehensive Python GUI application for controlling all features of the Analog Discovery 2
Compatible with Python 3.10 32-bit

Dependencies:
- tkinter (built-in)
- matplotlib
- numpy
- dwf (pip install dwf)
- threading
"""

import sys
import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import threading
import time
import json
from datetime import datetime
from ctypes import cdll

# Define DWF_AVAILABLE and DwfLibrary simulation for demonstration
try:
    from dwf import DwfLibrary
    DWF_AVAILABLE = True
except ImportError:
    DWF_AVAILABLE = False

class AnalogDiscovery2GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analog Discovery 2 - Complete Control Interface")
        self.root.geometry("1400x900")

        # Initialize variables
        self.device = None
        self.is_connected = False
        self.is_acquiring = False
        self.acquisition_thread = None

        # Data storage
        self.scope_data = {'ch1': [], 'ch2': [], 'time': []}
        self.spectrum_data = {'frequency': [], 'magnitude': []}

        # Initialize variables used in methods but missing
        self.data_logger_running = False
        self.logger_thread = None
        self.spectrum_running = False
        self.spectrum_thread = None
        self.na_running = False
        self.na_thread = None
        self.na_freq_data = []
        self.na_s11_mag_data = []
        self.na_s11_phase_data = []

        # Create main interface
        self.create_main_interface()

        # Initialize device connection
        self.initialize_device()

    def load_dwf_library(self):
        """Load the WaveForms library based on system architecture"""
        try:
            if sys.platform.startswith("win"):
                # For 32-bit Python on Windows
                if "32 bit" in sys.version or sys.maxsize <= 2 ** 32:
                    self.dwf = cdll.LoadLibrary("dwf.dll")
                else:
                    self.dwf = cdll.LoadLibrary("dwf.dll")  # Try default first
            elif sys.platform.startswith("darwin"):
                self.dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
            else:
                self.dwf = cdll.LoadLibrary("libdwf.so")

            self.status_label.config(text="WaveForms library loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load WaveForms library: {e}")
            self.status_label.config(text="WaveForms library not found")

    def view_log_file(self):
        filename = self.dl_filename.get()
        if os.path.exists(filename):
            os.startfile(filename)  # Windows only
        else:
            messagebox.showerror("Error", f"File not found: {filename}")

    def browse_log_file(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.dl_filename.delete(0, tk.END)
            self.dl_filename.insert(0, filename)

    def show_about(self):
        messagebox.showinfo("About", "Analog Discovery 2 Complete GUI\nVersion 1.0\nDeveloped by samyro14")

    def create_main_interface(self):
        """Create the main GUI interface with all AD2 features"""

        # Create main menu
        self.create_menu()

        # Create main frame with tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Create tabs for different instruments
        self.create_connection_tab()
        self.create_oscilloscope_tab()
        self.create_function_generator_tab()
        self.create_power_supply_tab()
        self.create_digital_io_tab()
        self.create_logic_analyzer_tab()
        self.create_spectrum_analyzer_tab()
        self.create_network_analyzer_tab()
        self.create_impedance_analyzer_tab()
        self.create_voltmeter_tab()
        self.create_data_logger_tab()
        self.create_script_editor_tab()

        # Status bar
        self.create_status_bar()

    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Configuration", command=self.save_config)
        file_menu.add_command(label="Load Configuration", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def export_data(self):
        """Export current data to file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if not filename:
                return

            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Export oscilloscope data
                if self.scope_data['time']:
                    writer.writerow(['Oscilloscope Data'])
                    writer.writerow(['Time', 'Channel 1', 'Channel 2'])
                    for i in range(len(self.scope_data['time'])):
                        writer.writerow([
                            self.scope_data['time'][i],
                            self.scope_data['ch1'][i] if i < len(self.scope_data['ch1']) else '',
                            self.scope_data['ch2'][i] if i < len(self.scope_data['ch2']) else ''
                        ])
                    writer.writerow([])  # Empty row separator

                # Export spectrum data
                if self.spectrum_data['frequency']:
                    writer.writerow(['Spectrum Data'])
                    writer.writerow(['Frequency', 'Magnitude'])
                    for i in range(len(self.spectrum_data['frequency'])):
                        writer.writerow([
                            self.spectrum_data['frequency'][i],
                            self.spectrum_data['magnitude'][i]
                        ])
                    writer.writerow([])

                # Export network analyzer data if available
                if hasattr(self, 'na_freq_data') and self.na_freq_data:
                    writer.writerow(['Network Analyzer Data'])
                    writer.writerow(['Frequency', 'Magnitude', 'Phase'])
                    for i in range(len(self.na_freq_data)):
                        writer.writerow([
                            self.na_freq_data[i],
                            self.na_s11_mag_data[i] if i < len(self.na_s11_mag_data) else '',
                            self.na_s11_phase_data[i] if i < len(self.na_s11_phase_data) else ''
                        ])

            messagebox.showinfo("Success", f"Data exported to {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def save_config(self):
        """Save current settings to file"""
        try:
            settings = {
                # Add relevant settings here, example:
                'oscilloscope': {
                    'ch1_range': self.ch1_range.get(),
                    'ch2_range': self.ch2_range.get(),
                    'sample_rate': self.sample_rate.get(),
                    'buffer_size': self.buffer_size.get(),
                },
                # Add other settings as needed
            }
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w') as f:
                    json.dump(settings, f, indent=2)
                messagebox.showinfo("Success", "Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def load_config(self):
        """Load settings from file"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'r') as f:
                    settings = json.load(f)
                # Apply settings example:
                osc = settings.get('oscilloscope', {})
                if 'ch1_range' in osc:
                    self.ch1_range.set(osc['ch1_range'])
                if 'ch2_range' in osc:
                    self.ch2_range.set(osc['ch2_range'])
                if 'sample_rate' in osc:
                    self.sample_rate.set(osc['sample_rate'])
                if 'buffer_size' in osc:
                    self.buffer_size.set(osc['buffer_size'])
                # Apply other settings as needed
                messagebox.showinfo("Success", "Settings loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings: {str(e)}")

        # Device menu
        device_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Device", menu=device_menu)
        device_menu.add_command(label="Connect", command=self.connect_device)
        device_menu.add_command(label="Disconnect", command=self.disconnect_device)
        device_menu.add_command(label="Device Info", command=self.update_device_info)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_connection_tab(self):
        """Create device connection and status tab"""
        self.connection_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.connection_frame, text="Connection")

        # Connection controls
        conn_frame = ttk.LabelFrame(self.connection_frame, text="Device Connection")
        conn_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(conn_frame, text="Connect", command=self.connect_device).pack(side='left', padx=5)
        ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_device).pack(side='left', padx=5)

        self.connection_status = ttk.Label(conn_frame, text="Not Connected", foreground="red")
        self.connection_status.pack(side='left', padx=20)

        # Device information
        info_frame = ttk.LabelFrame(self.connection_frame, text="Device Information")
        info_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.device_info_text = tk.Text(info_frame, height=20)
        scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=self.device_info_text.yview)
        self.device_info_text.configure(yscrollcommand=scrollbar.set)

        self.device_info_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # System monitor
        monitor_frame = ttk.LabelFrame(self.connection_frame, text="System Monitor")
        monitor_frame.pack(fill='x', padx=10, pady=5)

        self.voltage_label = ttk.Label(monitor_frame, text="Voltage: -- V")
        self.voltage_label.pack(side='left', padx=10)

        self.current_label = ttk.Label(monitor_frame, text="Current: -- mA")
        self.current_label.pack(side='left', padx=10)

        self.temp_label = ttk.Label(monitor_frame, text="Temperature: -- °C")
        self.temp_label.pack(side='left', padx=10)

    def create_oscilloscope_tab(self):
        """Create oscilloscope interface"""
        self.osc_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.osc_frame, text="Oscilloscope")

        # Control panel
        control_frame = ttk.LabelFrame(self.osc_frame, text="Oscilloscope Controls")
        control_frame.pack(fill='x', padx=10, pady=5)

        # Channel controls
        ch1_frame = ttk.LabelFrame(control_frame, text="Channel 1")
        ch1_frame.pack(side='left', fill='y', padx=5)

        ttk.Checkbutton(ch1_frame, text="Enable Ch1").pack(anchor='w')
        ttk.Label(ch1_frame, text="Range (V):").pack(anchor='w')
        self.ch1_range = ttk.Combobox(ch1_frame, values=['0.1', '0.2', '0.5', '1', '2', '5', '10', '20'])
        self.ch1_range.set('5')
        self.ch1_range.pack(fill='x', padx=2)

        ttk.Label(ch1_frame, text="Offset (V):").pack(anchor='w')
        self.ch1_offset = ttk.Scale(ch1_frame, from_=-5, to=5, orient='horizontal')
        self.ch1_offset.pack(fill='x', padx=2)

        ch2_frame = ttk.LabelFrame(control_frame, text="Channel 2")
        ch2_frame.pack(side='left', fill='y', padx=5)

        ttk.Checkbutton(ch2_frame, text="Enable Ch2").pack(anchor='w')
        ttk.Label(ch2_frame, text="Range (V):").pack(anchor='w')
        self.ch2_range = ttk.Combobox(ch2_frame, values=['0.1', '0.2', '0.5', '1', '2', '5', '10', '20'])
        self.ch2_range.set('5')
        self.ch2_range.pack(fill='x', padx=2)

        ttk.Label(ch2_frame, text="Offset (V):").pack(anchor='w')
        self.ch2_offset = ttk.Scale(ch2_frame, from_=-5, to=5, orient='horizontal')
        self.ch2_offset.pack(fill='x', padx=2)

        # Time base controls
        time_frame = ttk.LabelFrame(control_frame, text="Time Base")
        time_frame.pack(side='left', fill='y', padx=5)

        ttk.Label(time_frame, text="Sample Rate:").pack(anchor='w')
        self.sample_rate = ttk.Combobox(time_frame, values=['1000', '10000', '100000', '1000000', '10000000'])
        self.sample_rate.set('100000')
        self.sample_rate.pack(fill='x', padx=2)

        ttk.Label(time_frame, text="Buffer Size:").pack(anchor='w')
        self.buffer_size = ttk.Combobox(time_frame, values=['1024', '2048', '4096', '8192', '16384'])
        self.buffer_size.set('4096')
        self.buffer_size.pack(fill='x', padx=2)

        # Trigger controls
        trigger_frame = ttk.LabelFrame(control_frame, text="Trigger")
        trigger_frame.pack(side='left', fill='y', padx=5)

        ttk.Label(trigger_frame, text="Source:").pack(anchor='w')
        self.trigger_source = ttk.Combobox(trigger_frame, values=['Ch1', 'Ch2', 'External'])
        self.trigger_source.set('Ch1')
        self.trigger_source.pack(fill='x', padx=2)

        ttk.Label(trigger_frame, text="Level (V):").pack(anchor='w')
        self.trigger_level = ttk.Scale(trigger_frame, from_=-5, to=5, orient='horizontal')
        self.trigger_level.pack(fill='x', padx=2)

        ttk.Label(trigger_frame, text="Edge:").pack(anchor='w')
        self.trigger_edge = ttk.Combobox(trigger_frame, values=['Rising', 'Falling', 'Both'])
        self.trigger_edge.set('Rising')
        self.trigger_edge.pack(fill='x', padx=2)

        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side='left', fill='y', padx=10)

        ttk.Button(button_frame, text="Start", command=self.start_oscilloscope).pack(pady=2)
        ttk.Button(button_frame, text="Stop", command=self.stop_oscilloscope).pack(pady=2)
        ttk.Button(button_frame, text="Single", command=self.single_capture).pack(pady=2)
        ttk.Button(button_frame, text="Auto Scale", command=self.auto_scale).pack(pady=2)

        # Plot area
        self.create_oscilloscope_plot()

    def create_oscilloscope_plot(self):
        """Create oscilloscope plot area"""
        plot_frame = ttk.LabelFrame(self.osc_frame, text="Waveform Display")
        plot_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.osc_fig = Figure(figsize=(12, 6), dpi=100)
        self.osc_ax = self.osc_fig.add_subplot(111)
        self.osc_ax.set_xlabel('Time (s)')
        self.osc_ax.set_ylabel('Voltage (V)')
        self.osc_ax.grid(True)

        self.osc_canvas = FigureCanvasTkAgg(self.osc_fig, plot_frame)
        self.osc_canvas.draw()
        self.osc_canvas.get_tk_widget().pack(fill='both', expand=True)

    def create_function_generator_tab(self):
        """Create function generator interface"""
        self.fg_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.fg_frame, text="Function Generator")

        # Channel 1 controls
        ch1_frame = ttk.LabelFrame(self.fg_frame, text="Channel 1")
        ch1_frame.pack(fill='x', padx=10, pady=5)

        ch1_left = ttk.Frame(ch1_frame)
        ch1_left.pack(side='left', fill='y', padx=10)

        ttk.Checkbutton(ch1_left, text="Enable Channel 1").pack(anchor='w')

        ttk.Label(ch1_left, text="Waveform:").pack(anchor='w')
        self.fg_ch1_waveform = ttk.Combobox(ch1_left, values=['Sine', 'Square', 'Triangle', 'Sawtooth', 'DC', 'Noise'])
        self.fg_ch1_waveform.set('Sine')
        self.fg_ch1_waveform.pack(fill='x', pady=2)

        ttk.Label(ch1_left, text="Frequency (Hz):").pack(anchor='w')
        self.fg_ch1_freq = ttk.Entry(ch1_left)
        self.fg_ch1_freq.insert(0, '1000')
        self.fg_ch1_freq.pack(fill='x', pady=2)

        ch1_right = ttk.Frame(ch1_frame)
        ch1_right.pack(side='left', fill='y', padx=10)

        ttk.Label(ch1_right, text="Amplitude (V):").pack(anchor='w')
        self.fg_ch1_amp = ttk.Entry(ch1_right)
        self.fg_ch1_amp.insert(0, '1.0')
        self.fg_ch1_amp.pack(fill='x', pady=2)

        ttk.Label(ch1_right, text="Offset (V):").pack(anchor='w')
        self.fg_ch1_offset = ttk.Entry(ch1_right)
        self.fg_ch1_offset.insert(0, '0.0')
        self.fg_ch1_offset.pack(fill='x', pady=2)

        ttk.Label(ch1_right, text="Phase (°):").pack(anchor='w')
        self.fg_ch1_phase = ttk.Entry(ch1_right)
        self.fg_ch1_phase.insert(0, '0')
        self.fg_ch1_phase.pack(fill='x', pady=2)

        # Channel 2 controls (similar to Channel 1)
        ch2_frame = ttk.LabelFrame(self.fg_frame, text="Channel 2")
        ch2_frame.pack(fill='x', padx=10, pady=5)

        ch2_left = ttk.Frame(ch2_frame)
        ch2_left.pack(side='left', fill='y', padx=10)

        ttk.Checkbutton(ch2_left, text="Enable Channel 2").pack(anchor='w')

        ttk.Label(ch2_left, text="Waveform:").pack(anchor='w')
        self.fg_ch2_waveform = ttk.Combobox(ch2_left, values=['Sine', 'Square', 'Triangle', 'Sawtooth', 'DC', 'Noise'])
        self.fg_ch2_waveform.set('Sine')
        self.fg_ch2_waveform.pack(fill='x', pady=2)

        ttk.Label(ch2_left, text="Frequency (Hz):").pack(anchor='w')
        self.fg_ch2_freq = ttk.Entry(ch2_left)
        self.fg_ch2_freq.insert(0, '2000')
        self.fg_ch2_freq.pack(fill='x', pady=2)

        ch2_right = ttk.Frame(ch2_frame)
        ch2_right.pack(side='left', fill='y', padx=10)

        ttk.Label(ch2_right, text="Amplitude (V):").pack(anchor='w')
        self.fg_ch2_amp = ttk.Entry(ch2_right)
        self.fg_ch2_amp.insert(0, '1.0')
        self.fg_ch2_amp.pack(fill='x', pady=2)

        ttk.Label(ch2_right, text="Offset (V):").pack(anchor='w')
        self.fg_ch2_offset = ttk.Entry(ch2_right)
        self.fg_ch2_offset.insert(0, '0.0')
        self.fg_ch2_offset.pack(fill='x', pady=2)

        ttk.Label(ch2_right, text="Phase (°):").pack(anchor='w')
        self.fg_ch2_phase = ttk.Entry(ch2_right)
        self.fg_ch2_phase.insert(0, '0')
        self.fg_ch2_phase.pack(fill='x', pady=2)

        # Control buttons
        control_frame = ttk.Frame(self.fg_frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(control_frame, text="Start Both Channels", command=self.start_function_generator).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Stop Both Channels", command=self.stop_function_generator).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Load Arbitrary Waveform", command=self.load_arbitrary_waveform).pack(side='left', padx=5)

    def create_power_supply_tab(self):
        """Create power supply interface"""
        self.ps_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ps_frame, text="Power Supply")

        # Positive supply
        pos_frame = ttk.LabelFrame(self.ps_frame, text="Positive Supply")
        pos_frame.pack(fill='x', padx=10, pady=5)

        ttk.Checkbutton(pos_frame, text="Enable Positive Supply").pack(anchor='w')

        ttk.Label(pos_frame, text="Voltage (V):").pack(anchor='w')
        self.ps_pos_voltage = ttk.Scale(pos_frame, from_=0, to=5, orient='horizontal')
        self.ps_pos_voltage.set(3.3)
        self.ps_pos_voltage.pack(fill='x', padx=10)

        self.ps_pos_voltage_label = ttk.Label(pos_frame, text="3.3 V")
        self.ps_pos_voltage_label.pack()

        # Negative supply
        neg_frame = ttk.LabelFrame(self.ps_frame, text="Negative Supply")
        neg_frame.pack(fill='x', padx=10, pady=5)

        ttk.Checkbutton(neg_frame, text="Enable Negative Supply").pack(anchor='w')

        ttk.Label(neg_frame, text="Voltage (V):").pack(anchor='w')
        self.ps_neg_voltage = ttk.Scale(neg_frame, from_=-5, to=0, orient='horizontal')
        self.ps_neg_voltage.set(-3.3)
        self.ps_neg_voltage.pack(fill='x', padx=10)

        self.ps_neg_voltage_label = ttk.Label(neg_frame, text="-3.3 V")
        self.ps_neg_voltage_label.pack()

        # Current monitoring
        monitor_frame = ttk.LabelFrame(self.ps_frame, text="Current Monitoring")
        monitor_frame.pack(fill='x', padx=10, pady=5)

        self.ps_pos_current = ttk.Label(monitor_frame, text="Positive Current: -- mA")
        self.ps_pos_current.pack(anchor='w')

        self.ps_neg_current = ttk.Label(monitor_frame, text="Negative Current: -- mA")
        self.ps_neg_current.pack(anchor='w')

        # Control buttons
        control_frame = ttk.Frame(self.ps_frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(control_frame, text="Apply Settings", command=self.apply_power_supply).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Turn Off All", command=self.turn_off_power_supply).pack(side='left', padx=5)

    def create_digital_io_tab(self):
        """Create digital I/O interface"""
        self.dio_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dio_frame, text="Digital I/O")

        # Digital output controls
        output_frame = ttk.LabelFrame(self.dio_frame, text="Digital Outputs")
        output_frame.pack(fill='x', padx=10, pady=5)

        self.dio_outputs = {}
        for i in range(16):
            frame = ttk.Frame(output_frame)
            frame.pack(fill='x', padx=5, pady=2)

            ttk.Label(frame, text=f"DIO {i}:").pack(side='left')

            var = tk.BooleanVar()
            self.dio_outputs[i] = var
            ttk.Checkbutton(frame, text="High", variable=var).pack(side='left', padx=10)

            ttk.Label(frame, text="Mode:").pack(side='left', padx=10)
            mode_combo = ttk.Combobox(frame, values=['Output', 'Input', 'Input Pull-Up', 'Input Pull-Down'], width=15)
            mode_combo.set('Output')
            mode_combo.pack(side='left', padx=5)

        # Digital input monitoring
        input_frame = ttk.LabelFrame(self.dio_frame, text="Digital Input Status")
        input_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.dio_input_text = tk.Text(input_frame, height=10)
        dio_scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=self.dio_input_text.yview)
        self.dio_input_text.configure(yscrollcommand=dio_scrollbar.set)

        self.dio_input_text.pack(side="left", fill="both", expand=True)
        dio_scrollbar.pack(side="right", fill="y")

        # Control buttons
        control_frame = ttk.Frame(self.dio_frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(control_frame, text="Apply Outputs", command=self.apply_digital_outputs).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Read Inputs", command=self.read_digital_inputs).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Start Monitoring", command=self.start_digital_monitoring).pack(side='left', padx=5)

    def create_logic_analyzer_tab(self):
        """Create logic analyzer interface"""
        self.la_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.la_frame, text="Logic Analyzer")

        # Configuration
        config_frame = ttk.LabelFrame(self.la_frame, text="Logic Analyzer Configuration")
        config_frame.pack(fill='x', padx=10, pady=5)

        left_config = ttk.Frame(config_frame)
        left_config.pack(side='left', fill='y', padx=10)

        ttk.Label(left_config, text="Sample Rate:").pack(anchor='w')
        self.la_sample_rate = ttk.Combobox(left_config, values=['1MHz', '10MHz', '100MHz'])
        self.la_sample_rate.set('10MHz')
        self.la_sample_rate.pack(fill='x', pady=2)

        ttk.Label(left_config, text="Buffer Size:").pack(anchor='w')
        self.la_buffer_size = ttk.Combobox(left_config, values=['1024', '2048', '4096', '8192'])
        self.la_buffer_size.set('4096')
        self.la_buffer_size.pack(fill='x', pady=2)

        right_config = ttk.Frame(config_frame)
        right_config.pack(side='left', fill='y', padx=10)

        ttk.Label(right_config, text="Trigger Channel:").pack(anchor='w')
        self.la_trigger_channel = ttk.Combobox(right_config, values=[f'DIO{i}' for i in range(16)])
        self.la_trigger_channel.set('DIO0')
        self.la_trigger_channel.pack(fill='x', pady=2)

        ttk.Label(right_config, text="Trigger Edge:").pack(anchor='w')
        self.la_trigger_edge = ttk.Combobox(right_config, values=['Rising', 'Falling', 'Both'])
        self.la_trigger_edge.set('Rising')
        self.la_trigger_edge.pack(fill='x', pady=2)

        # Channel selection
        channel_frame = ttk.LabelFrame(self.la_frame, text="Channel Selection")
        channel_frame.pack(fill='x', padx=10, pady=5)

        self.la_channels = {}
        for i in range(16):
            var = tk.BooleanVar()
            self.la_channels[i] = var
            ttk.Checkbutton(channel_frame, text=f"DIO{i}", variable=var).pack(side='left', padx=5)

        # Control buttons
        control_frame = ttk.Frame(self.la_frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(control_frame, text="Start Capture", command=self.start_logic_analyzer).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Stop Capture", command=self.stop_logic_analyzer).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Single Capture", command=self.single_logic_capture).pack(side='left', padx=5)

        # Display area
        self.create_logic_analyzer_plot()

    def create_logic_analyzer_plot(self):
        """Create logic analyzer plot area"""
        plot_frame = ttk.LabelFrame(self.la_frame, text="Logic Analyzer Display")
        plot_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.la_fig = Figure(figsize=(12, 6), dpi=100)
        self.la_ax = self.la_fig.add_subplot(111)
        self.la_ax.set_xlabel('Time (s)')
        self.la_ax.set_ylabel('Digital Channels')
        self.la_ax.grid(True)

        self.la_canvas = FigureCanvasTkAgg(self.la_fig, plot_frame)
        self.la_canvas.draw()
        self.la_canvas.get_tk_widget().pack(fill='both', expand=True)

    def create_spectrum_analyzer_tab(self):
        """Create spectrum analyzer interface"""
        self.sa_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sa_frame, text="Spectrum Analyzer")

        # Configuration
        config_frame = ttk.LabelFrame(self.sa_frame, text="Spectrum Analyzer Configuration")
        config_frame.pack(fill='x', padx=10, pady=5)

        left_config = ttk.Frame(config_frame)
        left_config.pack(side='left', fill='y', padx=10)

        ttk.Label(left_config, text="Channel:").pack(anchor='w')
        self.sa_channel = ttk.Combobox(left_config, values=['Ch1', 'Ch2'])
        self.sa_channel.set('Ch1')
        self.sa_channel.pack(fill='x', pady=2)

        ttk.Label(left_config, text="Window:").pack(anchor='w')
        self.sa_window = ttk.Combobox(left_config, values=['Rectangular', 'Hanning', 'Hamming', 'Blackman'])
        self.sa_window.set('Hanning')
        self.sa_window.pack(fill='x', pady=2)

        right_config = ttk.Frame(config_frame)
        right_config.pack(side='left', fill='y', padx=10)

        ttk.Label(right_config, text="Frequency Span:").pack(anchor='w')
        self.sa_span = ttk.Combobox(right_config, values=['1kHz', '10kHz', '100kHz', '1MHz', '10MHz'])
        self.sa_span.set('1MHz')
        self.sa_span.pack(fill='x', pady=2)

        ttk.Label(right_config, text="Center Frequency:").pack(anchor='w')
        self.sa_center_freq = ttk.Entry(right_config)
        self.sa_center_freq.insert(0, '1000000')
        self.sa_center_freq.pack(fill='x', pady=2)

        # Control buttons
        control_frame = ttk.Frame(self.sa_frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(control_frame, text="Start Analysis", command=self.start_spectrum_analyzer).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Stop Analysis", command=self.stop_spectrum_analyzer).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Peak Hold", command=self.peak_hold_spectrum).pack(side='left', padx=5)

        # Display area
        self.create_spectrum_analyzer_plot()

    def create_spectrum_analyzer_plot(self):
        """Create spectrum analyzer plot area"""
        plot_frame = ttk.LabelFrame(self.sa_frame, text="Spectrum Display")
        plot_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.sa_fig = Figure(figsize=(12, 6), dpi=100)
        self.sa_ax = self.sa_fig.add_subplot(111)
        self.sa_ax.set_xlabel('Frequency (Hz)')
        self.sa_ax.set_ylabel('Magnitude (dB)')
        self.sa_ax.grid(True)

        self.sa_canvas = FigureCanvasTkAgg(self.sa_fig, plot_frame)
        self.sa_canvas.draw()
        self.sa_canvas.get_tk_widget().pack(fill='both', expand=True)

    def create_network_analyzer_tab(self):
        """Create network analyzer interface"""
        self.na_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.na_frame, text="Network Analyzer")

        # Configuration
        config_frame = ttk.LabelFrame(self.na_frame, text="Network Analyzer Configuration")
        config_frame.pack(fill='x', padx=10, pady=5)

        left_config = ttk.Frame(config_frame)
        left_config.pack(side='left', fill='y', padx=10)

        ttk.Label(left_config, text="Start Frequency (Hz):").pack(anchor='w')
        self.na_start_freq = ttk.Entry(left_config)
        self.na_start_freq.insert(0, '100')
        self.na_start_freq.pack(fill='x', pady=2)

        ttk.Label(left_config, text="Stop Frequency (Hz):").pack(anchor='w')
        self.na_stop_freq = ttk.Entry(left_config)
        self.na_stop_freq.insert(0, '1000000')
        self.na_stop_freq.pack(fill='x', pady=2)

        right_config = ttk.Frame(config_frame)
        right_config.pack(side='left', fill='y', padx=10)

        ttk.Label(right_config, text="Number of Steps:").pack(anchor='w')
        self.na_steps = ttk.Entry(right_config)
        self.na_steps.insert(0, '100')
        self.na_steps.pack(fill='x', pady=2)

        ttk.Label(right_config, text="Amplitude (V):").pack(anchor='w')
        self.na_amplitude = ttk.Entry(right_config)
        self.na_amplitude.insert(0, '1.0')
        self.na_amplitude.pack(fill='x', pady=2)

        # Measurement type
        meas_frame = ttk.LabelFrame(self.na_frame, text="Measurement Type")
        meas_frame.pack(fill='x', padx=10, pady=5)

        self.na_measurement = tk.StringVar(value="Magnitude")
        ttk.Radiobutton(meas_frame, text="Magnitude", variable=self.na_measurement, value="Magnitude").pack(side='left', padx=10)
        ttk.Radiobutton(meas_frame, text="Phase", variable=self.na_measurement, value="Phase").pack(side='left', padx=10)
        ttk.Radiobutton(meas_frame, text="Both", variable=self.na_measurement, value="Both").pack(side='left', padx=10)

        # Control buttons
        control_frame = ttk.Frame(self.na_frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(control_frame, text="Start Sweep", command=self.start_network_analyzer).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Stop Sweep", command=self.stop_network_analyzer).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Single Sweep", command=self.single_network_sweep).pack(side='left', padx=5)

        # Display area
        self.create_network_analyzer_plot()

    def create_network_analyzer_plot(self):
        """Create network analyzer plot area"""
        plot_frame = ttk.LabelFrame(self.na_frame, text="Network Analysis Display")
        plot_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.na_fig = Figure(figsize=(12, 6), dpi=100)
        self.na_ax1 = self.na_fig.add_subplot(211)
        self.na_ax2 = self.na_fig.add_subplot(212)

        self.na_ax1.set_ylabel('Magnitude (dB)')
        self.na_ax1.grid(True)
        self.na_ax2.set_xlabel('Frequency (Hz)')
        self.na_ax2.set_ylabel('Phase (°)')
        self.na_ax2.grid(True)

        self.na_canvas = FigureCanvasTkAgg(self.na_fig, plot_frame)
        self.na_canvas.draw()
        self.na_canvas.get_tk_widget().pack(fill='both', expand=True)

    def create_impedance_analyzer_tab(self):
        """Create impedance analyzer interface"""
        self.ia_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ia_frame, text="Impedance Analyzer")

        # Configuration
        config_frame = ttk.LabelFrame(self.ia_frame, text="Impedance Analyzer Configuration")
        config_frame.pack(fill='x', padx=10, pady=5)

        left_config = ttk.Frame(config_frame)
        left_config.pack(side='left', fill='y', padx=10)

        ttk.Label(left_config, text="Test Frequency (Hz):").pack(anchor='w')
        self.ia_frequency = ttk.Entry(left_config)
        self.ia_frequency.insert(0, '1000')
        self.ia_frequency.pack(fill='x', pady=2)

        ttk.Label(left_config, text="Test Amplitude (V):").pack(anchor='w')
        self.ia_amplitude = ttk.Entry(left_config)
        self.ia_amplitude.insert(0, '1.0')
        self.ia_amplitude.pack(fill='x', pady=2)

        right_config = ttk.Frame(config_frame)
        right_config.pack(side='left', fill='y', padx=10)

        ttk.Label(right_config, text="Reference Resistor (Ω):").pack(anchor='w')
        self.ia_ref_resistor = ttk.Entry(right_config)
        self.ia_ref_resistor.insert(0, '1000')
        self.ia_ref_resistor.pack(fill='x', pady=2)

        ttk.Label(right_config, text="Measurement Range:").pack(anchor='w')
        self.ia_range = ttk.Combobox(right_config, values=['Auto', '1Ω-1kΩ', '1kΩ-1MΩ', '1MΩ-1GΩ'])
        self.ia_range.set('Auto')
        self.ia_range.pack(fill='x', pady=2)

        # Results display
        results_frame = ttk.LabelFrame(self.ia_frame, text="Measurement Results")
        results_frame.pack(fill='x', padx=10, pady=5)

        self.ia_impedance_label = ttk.Label(results_frame, text="Impedance: -- Ω")
        self.ia_impedance_label.pack(anchor='w', padx=10)

        self.ia_phase_label = ttk.Label(results_frame, text="Phase: -- °")
        self.ia_phase_label.pack(anchor='w', padx=10)

        self.ia_resistance_label = ttk.Label(results_frame, text="Resistance: -- Ω")
        self.ia_resistance_label.pack(anchor='w', padx=10)

        self.ia_reactance_label = ttk.Label(results_frame, text="Reactance: -- Ω")
        self.ia_reactance_label.pack(anchor='w', padx=10)

        # Control buttons
        control_frame = ttk.Frame(self.ia_frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(control_frame, text="Measure", command=self.measure_impedance).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Continuous", command=self.continuous_impedance).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Calibrate", command=self.calibrate_impedance).pack(side='left', padx=5)

    def create_voltmeter_tab(self):
        """Create voltmeter interface"""
        self.vm_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.vm_frame, text="Voltmeter")

        # Channel configuration
        config_frame = ttk.LabelFrame(self.vm_frame, text="Voltmeter Configuration")
        config_frame.pack(fill='x', padx=10, pady=5)

        left_config = ttk.Frame(config_frame)
        left_config.pack(side='left', fill='y', padx=10)

        ttk.Label(left_config, text="Channel 1 Range:").pack(anchor='w')
        self.vm_ch1_range = ttk.Combobox(left_config, values=['±25V', '±2.5V', '±250mV'])
        self.vm_ch1_range.set('±25V')
        self.vm_ch1_range.pack(fill='x', pady=2)

        ttk.Label(left_config, text="Channel 2 Range:").pack(anchor='w')
        self.vm_ch2_range = ttk.Combobox(left_config, values=['±25V', '±2.5V', '±250mV'])
        self.vm_ch2_range.set('±25V')
        self.vm_ch2_range.pack(fill='x', pady=2)

        right_config = ttk.Frame(config_frame)
        right_config.pack(side='left', fill='y', padx=10)

        ttk.Label(right_config, text="Sample Rate:").pack(anchor='w')
        self.vm_sample_rate = ttk.Combobox(right_config, values=['1 Hz', '10 Hz', '100 Hz', '1000 Hz'])
        self.vm_sample_rate.set('10 Hz')
        self.vm_sample_rate.pack(fill='x', pady=2)
if __name__ == "__main__":
    root = tk.Tk()
    app = AnalogDiscovery2GUI(root)
    root.mainloop()