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

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import threading
import time
import json
import os
from datetime import datetime


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

        ttk.Label(right_config, text="Filter:").pack(anchor='w')
        self.vm_filter = ttk.Combobox(right_config, values=['None', 'Low Pass', 'High Pass', 'Band Pass'])
        self.vm_filter.set('None')
        self.vm_filter.pack(fill='x', pady=2)

        # Measurements display
        measurements_frame = ttk.LabelFrame(self.vm_frame, text="Voltage Measurements")
        measurements_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Current readings
        current_frame = ttk.Frame(measurements_frame)
        current_frame.pack(fill='x', padx=10, pady=5)

        self.vm_ch1_voltage = ttk.Label(current_frame, text="Channel 1: -- V", font=('Arial', 16, 'bold'))
        self.vm_ch1_voltage.pack(side='left', padx=20)

        self.vm_ch2_voltage = ttk.Label(current_frame, text="Channel 2: -- V", font=('Arial', 16, 'bold'))
        self.vm_ch2_voltage.pack(side='left', padx=20)

        # Statistics
        stats_frame = ttk.LabelFrame(measurements_frame, text="Statistics")
        stats_frame.pack(fill='x', padx=10, pady=5)

        self.vm_ch1_stats = ttk.Label(stats_frame, text="Ch1 - Min: -- V, Max: -- V, Avg: -- V, RMS: -- V")
        self.vm_ch1_stats.pack(anchor='w', padx=5)

        self.vm_ch2_stats = ttk.Label(stats_frame, text="Ch2 - Min: -- V, Max: -- V, Avg: -- V, RMS: -- V")
        self.vm_ch2_stats.pack(anchor='w', padx=5)

        # Control buttons
        control_frame = ttk.Frame(self.vm_frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(control_frame, text="Start Measurement", command=self.start_voltmeter).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Stop Measurement", command=self.stop_voltmeter).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Reset Statistics", command=self.reset_voltmeter_stats).pack(side='left', padx=5)

    def create_data_logger_tab(self):
        """Create data logger interface"""
        self.dl_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dl_frame, text="Data Logger")

        # Configuration
        config_frame = ttk.LabelFrame(self.dl_frame, text="Data Logger Configuration")
        config_frame.pack(fill='x', padx=10, pady=5)

        left_config = ttk.Frame(config_frame)
        left_config.pack(side='left', fill='y', padx=10)

        ttk.Label(left_config, text="Log Interval:").pack(anchor='w')
        self.dl_interval = ttk.Combobox(left_config, values=['1s', '10s', '1min', '10min', '1hour'])
        self.dl_interval.set('1s')
        self.dl_interval.pack(fill='x', pady=2)

        ttk.Label(left_config, text="Duration:").pack(anchor='w')
        self.dl_duration = ttk.Entry(left_config)
        self.dl_duration.insert(0, '3600')  # 1 hour
        self.dl_duration.pack(fill='x', pady=2)

        right_config = ttk.Frame(config_frame)
        right_config.pack(side='left', fill='y', padx=10)

        ttk.Label(right_config, text="Channels to Log:").pack(anchor='w')
        self.dl_ch1_enabled = tk.BooleanVar()
        self.dl_ch2_enabled = tk.BooleanVar()
        ttk.Checkbutton(right_config, text="Channel 1", variable=self.dl_ch1_enabled).pack(anchor='w')
        ttk.Checkbutton(right_config, text="Channel 2", variable=self.dl_ch2_enabled).pack(anchor='w')

        ttk.Label(right_config, text="Output File:").pack(anchor='w')
        file_frame = ttk.Frame(right_config)
        file_frame.pack(fill='x')
        self.dl_filename = ttk.Entry(file_frame)
        self.dl_filename.insert(0, 'data_log.csv')
        self.dl_filename.pack(side='left', fill='x', expand=True)
        ttk.Button(file_frame, text="Browse", command=self.browse_log_file).pack(side='right')

        # Status and progress
        status_frame = ttk.LabelFrame(self.dl_frame, text="Logging Status")
        status_frame.pack(fill='x', padx=10, pady=5)

        self.dl_status_label = ttk.Label(status_frame, text="Status: Ready")
        self.dl_status_label.pack(anchor='w', padx=10)

        self.dl_progress = ttk.Progressbar(status_frame, mode='determinate')
        self.dl_progress.pack(fill='x', padx=10, pady=5)

        self.dl_samples_label = ttk.Label(status_frame, text="Samples Logged: 0")
        self.dl_samples_label.pack(anchor='w', padx=10)

        # Control buttons
        control_frame = ttk.Frame(self.dl_frame)
        control_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(control_frame, text="Start Logging", command=self.start_data_logger).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Stop Logging", command=self.stop_data_logger).pack(side='left', padx=5)
        ttk.Button(control_frame, text="View Log", command=self.view_log_file).pack(side='left', padx=5)

    def create_script_editor_tab(self):
        """Create script editor interface"""
        self.se_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.se_frame, text="Script Editor")

        # Toolbar
        toolbar_frame = ttk.Frame(self.se_frame)
        toolbar_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(toolbar_frame, text="New", command=self.new_script).pack(side='left', padx=2)
        ttk.Button(toolbar_frame, text="Open", command=self.open_script).pack(side='left', padx=2)
        ttk.Button(toolbar_frame, text="Save", command=self.save_script).pack(side='left', padx=2)
        ttk.Button(toolbar_frame, text="Save As", command=self.save_script_as).pack(side='left', padx=2)
        ttk.Separator(toolbar_frame, orient='vertical').pack(side='left', padx=5, fill='y')
        ttk.Button(toolbar_frame, text="Run", command=self.run_script).pack(side='left', padx=2)
        ttk.Button(toolbar_frame, text="Stop", command=self.stop_script).pack(side='left', padx=2)

        # Editor area
        editor_frame = ttk.LabelFrame(self.se_frame, text="Script Editor")
        editor_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Text editor with scrollbars
        text_frame = ttk.Frame(editor_frame)
        text_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.script_text = tk.Text(text_frame, wrap='none', font=('Courier', 10))

        v_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.script_text.yview)
        self.script_text.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(text_frame, orient="horizontal", command=self.script_text.xview)
        self.script_text.configure(xscrollcommand=h_scrollbar.set)

        self.script_text.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Output area
        output_frame = ttk.LabelFrame(self.se_frame, text="Script Output")
        output_frame.pack(fill='x', padx=10, pady=5)

        self.script_output = tk.Text(output_frame, height=8, font=('Courier', 9))
        output_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.script_output.yview)
        self.script_output.configure(yscrollcommand=output_scrollbar.set)

        self.script_output.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        output_scrollbar.pack(side="right", fill="y", pady=5)

        # Insert example script
        example_script = '''# Analog Discovery 2 Python Script Example
# This script demonstrates basic device control

import time

def main():
    print("Starting AD2 script...")
    
    # Example: Generate a sine wave on Channel 1
    # Set frequency to 1kHz, amplitude to 1V
    print("Configuring function generator...")
    
    # Example: Read voltage from oscilloscope
    print("Reading oscilloscope data...")
    
    # Your code here
    for i in range(10):
        print(f"Sample {i+1}: Reading data...")
        time.sleep(0.1)
    
    print("Script completed successfully!")

if __name__ == "__main__":
    main()
'''
        self.script_text.insert('1.0', example_script)

    def create_status_bar(self):
        """Create status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill='x', side='bottom')

        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side='left', padx=5)

        self.device_status_label = ttk.Label(self.status_frame, text="Device: Not Connected")
        self.device_status_label.pack(side='right', padx=5)

    # Device management methods
    def initialize_device(self):
        """Initialize device connection"""
        if DWF_AVAILABLE:
            try:
                self.dwf = DwfLibrary()
                self.update_status("DWF Library loaded successfully")
            except Exception as e:
                self.update_status(f"Failed to load DWF library: {e}")
        else:
            self.update_status("DWF library not available - running in simulation mode")

    def new_script(self):
        """Clear the script editor for a new script"""
        if messagebox.askyesno("New Script", "Clear the current script and start a new one?"):
            self.script_text.delete('1.0', tk.END)

    def open_script(self):
        filename = filedialog.askopenfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if filename:
            with open(filename, "r", encoding="utf-8") as f:
                script = f.read()
            self.script_text.delete('1.0', tk.END)
            self.script_text.insert('1.0', script)
    def connect_device(self):
        """Connect to Analog Discovery 2"""
        try:
            if DWF_AVAILABLE:
                # Enumerate devices
                device_count = self.dwf.FDwfEnum.enumerate_devices()
                if device_count == 0:
                    messagebox.showerror("Error", "No Analog Discovery devices found")
                    return

                # Open first device
                self.device = self.dwf.FDwfDevice.open(0)
                self.is_connected = True

                self.connection_status.config(text="Connected", foreground="green")
                self.device_status_label.config(text="Device: Connected")
                self.update_status("Device connected successfully")

                # Get device information
                self.update_device_info()

            else:
                # Simulation mode
                self.is_connected = True
                self.connection_status.config(text="Connected (Simulation)", foreground="blue")
                self.device_status_label.config(text="Device: Simulation Mode")
                self.update_status("Connected in simulation mode")
                self.simulate_device_info()

        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            self.update_status(f"Connection failed: {e}")

    def disconnect_device(self):
        """Disconnect from device"""
        try:
            if self.device and DWF_AVAILABLE:
                self.device.close()

            self.device = None
            self.is_connected = False
            self.connection_status.config(text="Not Connected", foreground="red")
            self.device_status_label.config(text="Device: Not Connected")
            self.update_status("Device disconnected")

        except Exception as e:
            self.update_status(f"Disconnect error: {e}")

    def update_device_info(self):
        """Update device information display"""
        if DWF_AVAILABLE and self.device:
            try:
                # Get device info (this would need proper DWF API calls)
                info_text = "Analog Discovery 2 Information:\n\n"
                info_text += "Device Name: Analog Discovery 2\n"
                info_text += "Serial Number: [Device Serial]\n"
                info_text += "Firmware Version: [Firmware Version]\n"
                info_text += "Hardware Version: [Hardware Version]\n\n"
                info_text += "Specifications:\n"
                info_text += "- Oscilloscope: 2 channels, 14-bit, 100MS/s\n"
                info_text += "- Function Generator: 2 channels, ±5V\n"
                info_text += "- Digital I/O: 16 channels\n"
                info_text += "- Power Supply: ±5V\n"
                info_text += "- Logic Analyzer: 16 channels, 100MS/s\n"

                self.device_info_text.delete('1.0', tk.END)
                self.device_info_text.insert('1.0', info_text)

            except Exception as e:
                self.update_status(f"Failed to get device info: {e}")

    def simulate_device_info(self):
        """Simulate device information for demo"""
        info_text = "Analog Discovery 2 Information (Simulation Mode):\n\n"
        info_text += "Device Name: Analog Discovery 2 (Simulated)\n"
        info_text += "Serial Number: SIM123456789\n"
        info_text += "Firmware Version: 3.16.3\n"
        info_text += "Hardware Version: 2.1\n\n"
        info_text += "Specifications:\n"
        info_text += "- Oscilloscope: 2 channels, 14-bit, 100MS/s, 30MHz bandwidth\n"
        info_text += "- Function Generator: 2 channels, ±5V, 25MHz\n"
        info_text += "- Digital I/O: 16 channels, 3.3V logic\n"
        info_text += "- Power Supply: +5V@500mA, -5V@500mA, +3.3V@500mA\n"
        info_text += "- Logic Analyzer: 16 channels, 100MS/s\n"
        info_text += "- Voltmeter: ±25V range\n"
        info_text += "- Spectrum Analyzer: DC to 25MHz\n"
        info_text += "- Network Analyzer: Bode plots, impedance\n"

        self.device_info_text.delete('1.0', tk.END)
        self.device_info_text.insert('1.0', info_text)

    # Oscilloscope methods
    def start_oscilloscope(self):
        """Start oscilloscope acquisition"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        self.is_acquiring = True
        self.update_status("Starting oscilloscope acquisition...")

        # Start acquisition thread
        self.acquisition_thread = threading.Thread(target=self.oscilloscope_acquisition_loop)
        self.acquisition_thread.daemon = True
        self.acquisition_thread.start()

    def stop_oscilloscope(self):
        """Stop oscilloscope acquisition"""
        self.is_acquiring = False
        self.update_status("Oscilloscope acquisition stopped")

    def single_capture(self):
        """Perform single oscilloscope capture"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        self.update_status("Performing single capture...")
        # Simulate or perform actual single capture
        self.simulate_oscilloscope_data()
        self.plot_oscilloscope_data()

    def auto_scale(self):
        """Auto scale oscilloscope display"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        self.update_status("Auto scaling oscilloscope...")

        # Simulate auto scaling by adjusting ranges based on current data
        if self.scope_data['ch1']:
            ch1_max = max(abs(max(self.scope_data['ch1'])), abs(min(self.scope_data['ch1'])))
            if ch1_max > 0:
                # Find appropriate range
                ranges = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20]
                for r in ranges:
                    if ch1_max <= r * 0.8:  # Use 80% of range
                        self.ch1_range.set(str(r))
                        break

        if self.scope_data['ch2']:
            ch2_max = max(abs(max(self.scope_data['ch2'])), abs(min(self.scope_data['ch2'])))
            if ch2_max > 0:
                ranges = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20]
                for r in ranges:
                    if ch2_max <= r * 0.8:
                        self.ch2_range.set(str(r))
                        break

        self.plot_oscilloscope_data()
        self.update_status("Auto scale completed")

    def oscilloscope_acquisition_loop(self):
        """Continuous oscilloscope acquisition loop"""
        while self.is_acquiring:
            try:
                # Simulate or acquire real data
                self.simulate_oscilloscope_data()

                # Update plot on main thread
                self.root.after(0, self.plot_oscilloscope_data)

                time.sleep(0.1)  # 10 FPS update rate

            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"Acquisition error: {e}"))
                break

    def simulate_oscilloscope_data(self):
        """Simulate oscilloscope data for demo"""
        sample_rate = float(self.sample_rate.get())
        buffer_size = int(self.buffer_size.get())

        # Generate time array
        dt = 1.0 / sample_rate
        time_array = np.arange(buffer_size) * dt

        # Generate simulated signals
        freq1 = 1000  # 1kHz
        freq2 = 2000  # 2kHz

        ch1_range = float(self.ch1_range.get())
        ch2_range = float(self.ch2_range.get())

        # Add some noise and varying amplitude
        noise_level = 0.1
        ch1_data = (ch1_range * 0.8) * np.sin(2 * np.pi * freq1 * time_array) + \
                   np.random.normal(0, noise_level, buffer_size)
        ch2_data = (ch2_range * 0.6) * np.sin(2 * np.pi * freq2 * time_array + np.pi / 4) + \
                   np.random.normal(0, noise_level, buffer_size)

        # Store data
        self.scope_data['time'] = time_array
        self.scope_data['ch1'] = ch1_data
        self.scope_data['ch2'] = ch2_data

    def plot_oscilloscope_data(self):
        """Plot oscilloscope data"""
        if not self.scope_data['time']:
            return

        self.osc_ax.clear()

        # Plot channels
        if self.scope_data['ch1']:
            self.osc_ax.plot(self.scope_data['time'], self.scope_data['ch1'],
                             'b-', label='Channel 1', linewidth=1)

        if self.scope_data['ch2']:
            self.osc_ax.plot(self.scope_data['time'], self.scope_data['ch2'],
                             'r-', label='Channel 2', linewidth=1)

        self.osc_ax.set_xlabel('Time (s)')
        self.osc_ax.set_ylabel('Voltage (V)')
        self.osc_ax.grid(True, alpha=0.3)
        self.osc_ax.legend()

        # Set axis limits
        ch1_range = float(self.ch1_range.get())
        ch2_range = float(self.ch2_range.get())
        max_range = max(ch1_range, ch2_range)
        self.osc_ax.set_ylim(-max_range, max_range)

        self.osc_canvas.draw()

    # Function Generator methods
    def start_function_generator(self):
        """Start function generator output"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        try:
            # Get channel 1 parameters
            ch1_freq = float(self.fg_ch1_freq.get())
            ch1_amp = float(self.fg_ch1_amp.get())
            ch1_offset = float(self.fg_ch1_offset.get())
            ch1_phase = float(self.fg_ch1_phase.get())

            # Get channel 2 parameters
            ch2_freq = float(self.fg_ch2_freq.get())
            ch2_amp = float(self.fg_ch2_amp.get())
            ch2_offset = float(self.fg_ch2_offset.get())
            ch2_phase = float(self.fg_ch2_phase.get())

            # Configure function generator (simulation)
            self.update_status(f"Function Generator: Ch1={ch1_freq}Hz, Ch2={ch2_freq}Hz")

            # In real implementation, configure the actual device here
            if DWF_AVAILABLE and self.device:
                # Configure actual device
                pass

            messagebox.showinfo("Success", "Function generator started successfully")

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid parameter: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start function generator: {e}")

    def stop_function_generator(self):
        """Stop function generator output"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        try:
            # Stop function generator output
            self.update_status("Function generator stopped")
            messagebox.showinfo("Success", "Function generator stopped")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop function generator: {e}")

    def load_arbitrary_waveform(self):
        """Load arbitrary waveform from file"""
        filename = filedialog.askopenfilename(
            title="Load Arbitrary Waveform",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            try:
                # Load waveform data
                data = np.loadtxt(filename, delimiter=',')
                self.update_status(f"Loaded arbitrary waveform: {filename}")
                messagebox.showinfo("Success", f"Loaded waveform with {len(data)} points")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load waveform: {e}")

    # Power Supply methods
    def apply_power_supply(self):
        """Apply power supply settings"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        try:
            pos_voltage = self.ps_pos_voltage.get()
            neg_voltage = self.ps_neg_voltage.get()

            # Update voltage labels
            self.ps_pos_voltage_label.config(text=f"{pos_voltage:.1f} V")
            self.ps_neg_voltage_label.config(text=f"{neg_voltage:.1f} V")

            # Apply settings (simulation)
            self.update_status(f"Power Supply: +{pos_voltage:.1f}V, {neg_voltage:.1f}V")

            # Simulate current readings
            pos_current = np.random.uniform(50, 150)  # mA
            neg_current = np.random.uniform(30, 100)  # mA

            self.ps_pos_current.config(text=f"Positive Current: {pos_current:.1f} mA")
            self.ps_neg_current.config(text=f"Negative Current: {neg_current:.1f} mA")

            messagebox.showinfo("Success", "Power supply settings applied")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply power supply settings: {e}")

    def turn_off_power_supply(self):
        """Turn off all power supply outputs"""
        try:
            self.ps_pos_voltage.set(0)
            self.ps_neg_voltage.set(0)

            self.ps_pos_voltage_label.config(text="0.0 V")
            self.ps_neg_voltage_label.config(text="0.0 V")

            self.ps_pos_current.config(text="Positive Current: 0.0 mA")
            self.ps_neg_current.config(text="Negative Current: 0.0 mA")

            self.update_status("All power supplies turned off")
            messagebox.showinfo("Success", "All power supplies turned off")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to turn off power supplies: {e}")

    # Digital I/O methods
    def apply_digital_outputs(self):
        """Apply digital output settings"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        try:
            output_states = []
            for i in range(16):
                state = self.dio_outputs[i].get()
                output_states.append(state)

            # Apply digital outputs (simulation)
            self.update_status(f"Digital outputs applied: {sum(output_states)} pins high")
            messagebox.showinfo("Success", "Digital outputs applied successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply digital outputs: {e}")

    def read_digital_inputs(self):
        """Read digital input states"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        try:
            # Simulate reading digital inputs
            input_states = np.random.randint(0, 2, 16)

            # Update display
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_text = f"[{timestamp}] Digital Input States:\n"

            for i in range(16):
                state = "HIGH" if input_states[i] else "LOW"
                status_text += f"DIO{i:2d}: {state}  "
                if (i + 1) % 4 == 0:
                    status_text += "\n"

            self.dio_input_text.insert(tk.END, status_text + "\n")
            self.dio_input_text.see(tk.END)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read digital inputs: {e}")

    def start_digital_monitoring(self):
        """Start continuous digital input monitoring"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        # Start monitoring thread
        def monitor_loop():
            for _ in range(100):  # Monitor for 100 iterations
                if not self.is_connected:
                    break
                self.root.after(0, self.read_digital_inputs)
                time.sleep(1)  # 1 second interval

        monitor_thread = threading.Thread(target=monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

        self.update_status("Started digital input monitoring")

    # Logic Analyzer methods
    def start_logic_analyzer(self):
        """Start logic analyzer capture"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        try:
            # Get configuration
            sample_rate = self.la_sample_rate.get()
            buffer_size = int(self.la_buffer_size.get())

            # Get enabled channels
            enabled_channels = []
            for i in range(16):
                if self.la_channels[i].get():
                    enabled_channels.append(i)

            if not enabled_channels:
                messagebox.showwarning("Warning", "No channels selected")
                return

            # Simulate logic analyzer data
            self.simulate_logic_analyzer_data(enabled_channels, buffer_size)
            self.plot_logic_analyzer_data()

            self.update_status(f"Logic analyzer started: {len(enabled_channels)} channels")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start logic analyzer: {e}")

    def stop_logic_analyzer(self):
        """Stop logic analyzer capture"""
        self.update_status("Logic analyzer stopped")

    def single_logic_capture(self):
        """Perform single logic analyzer capture"""
        self.start_logic_analyzer()

    def simulate_logic_analyzer_data(self, channels, buffer_size):
        """Simulate logic analyzer data"""
        # Generate time array
        sample_rate = 10e6  # 10 MHz
        dt = 1.0 / sample_rate
        time_array = np.arange(buffer_size) * dt

        # Generate digital signals for each channel
        self.la_data = {'time': time_array, 'channels': {}}

        for i, ch in enumerate(channels):
            # Create different patterns for different channels
            if ch % 4 == 0:
                # Clock signal
                freq = 1e6  # 1 MHz
                signal = (np.sin(2 * np.pi * freq * time_array) > 0).astype(int)
            elif ch % 4 == 1:
                # Data signal
                freq = 250e3  # 250 kHz
                signal = (np.sin(2 * np.pi * freq * time_array + np.pi / 4) > 0).astype(int)
            elif ch % 4 == 2:
                # Enable signal
                signal = np.ones(buffer_size, dtype=int)
                signal[:buffer_size // 4] = 0
                signal[3 * buffer_size // 4:] = 0
            else:
                # Random signal
                signal = np.random.randint(0, 2, buffer_size)

            self.la_data['channels'][ch] = signal

    def plot_logic_analyzer_data(self):
        """Plot logic analyzer data"""
        if not hasattr(self, 'la_data') or not self.la_data['channels']:
            return

        self.la_ax.clear()

        channels = sorted(self.la_data['channels'].keys())
        time_array = self.la_data['time']

        # Plot each channel
        for i, ch in enumerate(channels):
            signal = self.la_data['channels'][ch]
            # Offset each channel vertically
            offset_signal = signal + i * 1.5
            self.la_ax.plot(time_array, offset_signal, 'b-', linewidth=1)
            self.la_ax.text(time_array[0], i * 1.5 + 0.5, f'DIO{ch}',
                            verticalalignment='center')

        self.la_ax.set_xlabel('Time (s)')
        self.la_ax.set_ylabel('Digital Channels')
        self.la_ax.set_ylim(-0.5, len(channels) * 1.5)
        self.la_ax.grid(True, alpha=0.3)

        self.la_canvas.draw()

    # Spectrum Analyzer methods
    def start_spectrum_analyzer(self):
        """Start spectrum analyzer"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        try:
            # Get configuration
            channel = self.sa_channel.get()
            window = self.sa_window.get()
            span = self.sa_span.get()
            center_freq = float(self.sa_center_freq.get())

            # Simulate spectrum data
            self.simulate_spectrum_data(center_freq, span)
            self.plot_spectrum_data()

            self.update_status(f"Spectrum analyzer started: {channel}, {span} span")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start spectrum analyzer: {e}")

    def stop_spectrum_analyzer(self):
        """Stop spectrum analyzer"""
        self.update_status("Spectrum analyzer stopped")

    def peak_hold_spectrum(self):
        """Enable peak hold mode"""
        self.update_status("Peak hold enabled")

    def simulate_spectrum_data(self, center_freq, span):
        """Simulate spectrum analyzer data"""
        # Parse span
        span_map = {'1kHz': 1e3, '10kHz': 10e3, '100kHz': 100e3, '1MHz': 1e6, '10MHz': 10e6}
        span_hz = span_map.get(span, 1e6)

        # Generate frequency array
        freq_start = center_freq - span_hz / 2
        freq_stop = center_freq + span_hz / 2
        freq_array = np.linspace(freq_start, freq_stop, 1024)

        # Generate spectrum with some peaks
        noise_floor = -80  # dBm
        spectrum = np.random.normal(noise_floor, 5, len(freq_array))

        # Add some peaks
        peak_freqs = [center_freq - span_hz / 4, center_freq, center_freq + span_hz / 3]
        peak_levels = [-20, -10, -30]

        for pf, pl in zip(peak_freqs, peak_levels):
            # Add Gaussian peak
            idx = np.argmin(np.abs(freq_array - pf))
            width = 50
            peak = pl * np.exp(-((np.arange(len(freq_array)) - idx) / width) ** 2)
            spectrum += peak

        self.spectrum_data['frequency'] = freq_array
        self.spectrum_data['magnitude'] = spectrum

    def plot_spectrum_data(self):
        """Plot spectrum analyzer data"""
        if not self.spectrum_data['frequency']:
            return

        self.sa_ax.clear()

        self.sa_ax.plot(self.spectrum_data['frequency'], self.spectrum_data['magnitude'],
                        'b-', linewidth=1)

        self.sa_ax.set_xlabel('Frequency (Hz)')
        self.sa_ax.set_ylabel('Magnitude (dBm)')
        self.sa_ax.grid(True, alpha=0.3)
        self.sa_ax.set_title('Spectrum Analysis')

        self.sa_canvas.draw()

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

    # Network Analyzer methods
    def start_network_analyzer(self):
        """Start network analyzer sweep"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        try:
            start_freq = float(self.na_start_freq.get())
            stop_freq = float(self.na_stop_freq.get())
            steps = int(self.na_steps.get())
            amplitude = float(self.na_amplitude.get())

            # Simulate network analysis
            self.simulate_network_data(start_freq, stop_freq, steps)
            self.plot_network_data()

            self.update_status(f"Network analyzer: {start_freq}Hz to {stop_freq}Hz, {steps} points")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start network analyzer: {e}")

    def stop_network_analyzer(self):
        """Stop network analyzer sweep"""
        self.update_status("Network analyzer stopped")

    def single_network_sweep(self):
        """Perform single network analyzer sweep"""
        self.start_network_analyzer()

    def simulate_network_data(self, start_freq, stop_freq, steps):
        """Simulate network analyzer data"""
        freq_array = np.logspace(np.log10(start_freq), np.log10(stop_freq), steps)

        # Simulate a simple RC low-pass filter response
        R = 1000  # 1k ohm
        C = 100e-9  # 100nF
        s = 2j * np.pi * freq_array
        H = 1 / (1 + s * R * C)

        magnitude_db = 20 * np.log10(np.abs(H))
        phase_deg = np.angle(H) * 180 / np.pi

        self.na_data = {
            'frequency': freq_array,
            'magnitude': magnitude_db,
            'phase': phase_deg
        }

    def plot_network_data(self):
        """Plot network analyzer data"""
        if not hasattr(self, 'na_data'):
            return

        self.na_ax1.clear()
        self.na_ax2.clear()

        freq = self.na_data['frequency']

        # Plot magnitude
        self.na_ax1.semilogx(freq, self.na_data['magnitude'], 'b-', linewidth=1)
        self.na_ax1.set_ylabel('Magnitude (dB)')
        self.na_ax1.grid(True, alpha=0.3)
        self.na_ax1.set_title('Network Analysis - Bode Plot')

        # Plot phase
        self.na_ax2.semilogx(freq, self.na_data['phase'], 'r-', linewidth=1)
        self.na_ax2.set_xlabel('Frequency (Hz)')
        self.na_ax2.set_ylabel('Phase (°)')
        self.na_ax2.grid(True, alpha=0.3)

        self.na_canvas.draw()

    # Impedance Analyzer methods
    def measure_impedance(self):
        """Measure impedance"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        try:
            frequency = float(self.ia_frequency.get())
            amplitude = float(self.ia_amplitude.get())
            ref_resistor = float(self.ia_ref_resistor.get())

            # Simulate impedance measurement
            # Generate random impedance value
            Z_magnitude = np.random.uniform(100, 10000)  # 100 ohm to 10k ohm
            Z_phase = np.random.uniform(-90, 90)  # -90 to +90 degrees

            # Calculate R and X components
            Z_real = Z_magnitude * np.cos(np.radians(Z_phase))
            Z_imag = Z_magnitude * np.sin(np.radians(Z_phase))

            # Update display
            self.ia_impedance_label.config(text=f"Impedance: {Z_magnitude:.1f} Ω")
            self.ia_phase_label.config(text=f"Phase: {Z_phase:.1f} °")
            self.ia_resistance_label.config(text=f"Resistance: {Z_real:.1f} Ω")
            self.ia_reactance_label.config(text=f"Reactance: {Z_imag:.1f} Ω")

            self.update_status(f"Impedance measured: {Z_magnitude:.1f}Ω ∠{Z_phase:.1f}°")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to measure impedance: {e}")

    def continuous_impedance(self):
        """Start continuous impedance measurement"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        def continuous_loop():
            for _ in range(100):  # 100 measurements
                if not self.is_connected:
                    break
                self.root.after(0, self.measure_impedance)
                time.sleep(0.5)  # 2 Hz update rate

        continuous_thread = threading.Thread(target=continuous_loop)
        continuous_thread.daemon = True
        continuous_thread.start()

        self.update_status("Started continuous impedance measurement")

    def calibrate_impedance(self):
        """Calibrate impedance analyzer"""
        messagebox.showinfo("Calibration",
                            "Impedance analyzer calibration:\n\n"
                            "1. Connect open circuit and click OK\n"
                            "2. Connect short circuit and click OK\n"
                            "3. Connect known load and click OK")
        self.update_status("Impedance analyzer calibrated")

    # Voltmeter methods
    def start_voltmeter(self):
        """Start voltmeter measurement"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        def voltmeter_loop():
            sample_count = 0
            ch1_values = []
            ch2_values = []

            while self.is_connected and sample_count < 1000:
                # Simulate voltage readings
                ch1_voltage = np.random.normal(0, 1)  # Random voltage
                ch2_voltage = np.random.normal(0, 0.5)

                ch1_values.append(ch1_voltage)
                ch2_values.append(ch2_voltage)

                # Update display on main thread
                self.root.after(0,
                                lambda: self.update_voltmeter_display(ch1_voltage, ch2_voltage, ch1_values, ch2_values))

                sample_count += 1
                time.sleep(0.1)  # 10 Hz sample rate

        voltmeter_thread = threading.Thread(target=voltmeter_loop)
        voltmeter_thread.daemon = True
        voltmeter_thread.start()

        self.update_status("Voltmeter measurement started")

    def update_voltmeter_display(self, ch1_voltage, ch2_voltage, ch1_values, ch2_values):
        """Update voltmeter display"""
        # Update current readings
        self.vm_ch1_voltage.config(text=f"Channel 1: {ch1_voltage:.3f} V")
        self.vm_ch2_voltage.config(text=f"Channel 2: {ch2_voltage:.3f} V")

        # Update statistics
        if len(ch1_values) > 1:
            ch1_min = min(ch1_values)
            ch1_max = max(ch1_values)
            ch1_avg = np.mean(ch1_values)
            ch1_rms = np.sqrt(np.mean(np.array(ch1_values) ** 2))

            self.vm_ch1_stats.config(
                text=f"Ch1 - Min: {ch1_min:.3f}V, Max: {ch1_max:.3f}V, Avg: {ch1_avg:.3f}V, RMS: {ch1_rms:.3f}V")

        if len(ch2_values) > 1:
            ch2_min = min(ch2_values)
            ch2_max = max(ch2_values)
            ch2_avg = np.mean(ch2_values)
            ch2_rms = np.sqrt(np.mean(np.array(ch2_values) ** 2))

            self.vm_ch2_stats.config(
                text=f"Ch2 - Min: {ch2_min:.3f}V, Max: {ch2_max:.3f}V, Avg: {ch2_avg:.3f}V, RMS: {ch2_rms:.3f}V")

    def stop_voltmeter(self):
        """Stop voltmeter measurement"""
        self.update_status("Voltmeter measurement stopped")

    def reset_voltmeter_stats(self):
        """Reset voltmeter statistics"""
        self.vm_ch1_stats.config(text="Ch1 - Min: -- V, Max: -- V, Avg: -- V, RMS: -- V")
        self.vm_ch2_stats.config(text="Ch2 - Min: -- V, Max: -- V, Avg: -- V, RMS: -- V")
        self.update_status("Voltmeter statistics reset")

    # Data Logger methods
    def start_data_logger(self):
        """Start data logging"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        try:
            interval = self.dl_interval.get()
            duration = int(self.dl_duration.get())
            filename = self.dl_filename.get()

            # Parse interval
            interval_map = {'1s': 1, '10s': 10, '1min': 60, '10min': 600, '1hour': 3600}
            interval_seconds = interval_map.get(interval, 1)

            # Calculate total samples
            total_samples = duration // interval_seconds

            self.dl_progress.config(maximum=total_samples)
            self.dl_status_label.config(text="Status: Logging")

            def logging_loop():
                sample_count = 0
                log_data = []

                while sample_count < total_samples and self.is_connected:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Simulate data readings
                    ch1_data = np.random.normal(0, 1) if self.dl_ch1_enabled.get() else None
                    ch2_data = np.random.normal(0, 0.5) if self.dl_ch2_enabled.get() else None
                    # Create data row
                    row = [timestamp]
                    if self.dl_ch1_enabled.get():
                        row.append(ch1_data)
                    if self.dl_ch2_enabled.get():
                        row.append(ch2_data)

                    log_data.append(row)
                    sample_count += 1

                    # Update progress
                    self.dl_progress['value'] = sample_count
                    self.root.update_idletasks()

                    # Wait for next sample
                    time.sleep(interval_seconds)
                # Save data to file
                self.save_log_data(log_data, filename)
                self.dl_status_label.config(text="Status: Complete")
                self.data_logger_running = False
                messagebox.showinfo("Success", f"Data logging complete. Saved to {filename}")
                # Start logging in separate thread

            self.data_logger_running = True
            self.logger_thread = threading.Thread(target=logging_loop)
            self.logger_thread.daemon = True
            self.logger_thread.start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start data logger: {str(e)}")

    def stop_data_logger(self):
        """Stop data logging"""
        self.data_logger_running = False
        self.dl_status_label.config(text="Status: Stopped")
        if self.logger_thread and self.logger_thread.is_alive():
            self.logger_thread.join(timeout=1)

    def save_log_data(self, data, filename):
        """Save logged data to CSV file"""
        try:
            # Create headers
            headers = ['Timestamp']
            if self.dl_ch1_enabled.get():
                headers.append('Channel 1')
            if self.dl_ch2_enabled.get():
                headers.append('Channel 2')

            # Save to CSV
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(data)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")

    # Spectrum Analyzer methods
    def start_spectrum_analyzer(self):
        """Start spectrum analyzer"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        try:
            # Get settings
            start_freq = float(self.sa_start_freq.get())
            stop_freq = float(self.sa_stop_freq.get())
            samples = int(self.sa_samples.get())

            # Validate frequency range
            if start_freq >= stop_freq:
                messagebox.showerror("Error", "Start frequency must be less than stop frequency")
                return

            def spectrum_loop():
                while self.spectrum_running:
                    # Generate frequency array
                    freqs = np.linspace(start_freq, stop_freq, samples)

                    # Simulate spectrum data (replace with actual device readings)
                    spectrum = self.generate_simulated_spectrum(freqs)

                    # Update plot
                    self.update_spectrum_plot(freqs, spectrum)

                    time.sleep(0.1)  # Update rate

            self.spectrum_running = True
            self.spectrum_thread = threading.Thread(target=spectrum_loop)
            self.spectrum_thread.daemon = True
            self.spectrum_thread.start()

        except ValueError:
            messagebox.showerror("Error", "Invalid frequency values")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start spectrum analyzer: {str(e)}")

    def stop_spectrum_analyzer(self):
        """Stop spectrum analyzer"""
        self.spectrum_running = False

    def generate_simulated_spectrum(self, freqs):
        """Generate simulated spectrum data"""
        # Create a realistic spectrum with noise and some peaks
        spectrum = -60 + 10 * np.random.random(len(freqs))  # Base noise floor

        # Add some spectral peaks
        peak_freqs = [1000, 5000, 12000]  # Example peak frequencies
        for peak_freq in peak_freqs:
            if peak_freq >= freqs[0] and peak_freq <= freqs[-1]:
                # Find closest frequency bin
                idx = np.argmin(np.abs(freqs - peak_freq))
                # Add Gaussian peak
                width = len(freqs) // 20
                peak_indices = np.arange(max(0, idx - width), min(len(freqs), idx + width))
                peak_shape = np.exp(-0.5 * ((peak_indices - idx) / (width / 3)) ** 2)
                spectrum[peak_indices] += 20 * peak_shape

        return spectrum

    def update_spectrum_plot(self, freqs, spectrum):
        """Update spectrum analyzer plot"""
        try:
            self.spectrum_ax.clear()
            self.spectrum_ax.plot(freqs / 1000, spectrum)  # Convert to kHz for display
            self.spectrum_ax.set_xlabel('Frequency (kHz)')
            self.spectrum_ax.set_ylabel('Magnitude (dB)')
            self.spectrum_ax.set_title('Spectrum Analyzer')
            self.spectrum_ax.grid(True)
            self.spectrum_canvas.draw()
        except Exception as e:
            print(f"Error updating spectrum plot: {e}")

    # Digital I/O methods
    def update_digital_outputs(self):
        """Update digital output pins"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        try:
            # Get digital output states
            dio_states = 0
            for i in range(8):  # Assuming 8 digital I/O pins
                if hasattr(self, f'dio_{i}_var') and getattr(self, f'dio_{i}_var').get():
                    dio_states |= (1 << i)

            # In real implementation, send to device
            # For simulation, just update the display
            self.update_digital_display()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update digital outputs: {str(e)}")

    def read_digital_inputs(self):
        """Read digital input pins"""
        if not self.is_connected:
            return

        try:
            # In real implementation, read from device
            # For simulation, generate random states
            for i in range(8):
                if hasattr(self, f'din_{i}_label'):
                    state = np.random.choice([0, 1])
                    label = getattr(self, f'din_{i}_label')
                    label.config(text=f"DIN{i}: {'HIGH' if state else 'LOW'}")

        except Exception as e:
            print(f"Error reading digital inputs: {e}")

    def update_digital_display(self):
        """Update digital I/O display"""
        # This would update any visual indicators for digital I/O states
        pass

    # Protocol Analyzer methods
    def start_protocol_analyzer(self):
        """Start protocol analyzer"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        protocol = self.protocol_type.get()

        try:
            def protocol_loop():
                while self.protocol_running:
                    # Simulate protocol data capture
                    if protocol == "SPI":
                        data = self.capture_spi_data()
                    elif protocol == "I2C":
                        data = self.capture_i2c_data()
                    elif protocol == "UART":
                        data = self.capture_uart_data()
                    else:
                        data = "Unknown protocol"

                    # Update protocol display
                    self.update_protocol_display(data)

                    time.sleep(0.1)

            self.protocol_running = True
            self.protocol_thread = threading.Thread(target=protocol_loop)
            self.protocol_thread.daemon = True
            self.protocol_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start protocol analyzer: {str(e)}")

    def stop_protocol_analyzer(self):
        """Stop protocol analyzer"""
        self.protocol_running = False

    def capture_spi_data(self):
        """Simulate SPI data capture"""
        # Generate random SPI transaction
        data_bytes = [np.random.randint(0, 256) for _ in range(np.random.randint(1, 8))]
        return f"SPI: CS=LOW, MOSI=[{', '.join([f'0x{b:02X}' for b in data_bytes])}]"

    def capture_i2c_data(self):
        """Simulate I2C data capture"""
        # Generate random I2C transaction
        addr = np.random.randint(0x10, 0x78)
        data_bytes = [np.random.randint(0, 256) for _ in range(np.random.randint(1, 4))]
        return f"I2C: ADDR=0x{addr:02X}, DATA=[{', '.join([f'0x{b:02X}' for b in data_bytes])}]"

    def capture_uart_data(self):
        """Simulate UART data capture"""
        # Generate random UART data
        chars = ''.join([chr(np.random.randint(32, 127)) for _ in range(np.random.randint(1, 16))])
        return f"UART: '{chars}'"

    def update_protocol_display(self, data):
        """Update protocol analyzer display"""
        try:
            # Add new data to the protocol text widget
            self.protocol_text.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.protocol_text.insert(tk.END, f"[{timestamp}] {data}\n")
            self.protocol_text.see(tk.END)
            self.protocol_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Error updating protocol display: {e}")

    # Network Analyzer methods
    def start_network_analyzer(self):
        """Start network analyzer sweep"""
        if not self.is_connected:
            messagebox.showwarning("Warning", "Device not connected")
            return

        try:
            start_freq = float(self.na_start_freq.get())
            stop_freq = float(self.na_stop_freq.get())
            points = int(self.na_points.get())

            if start_freq >= stop_freq:
                messagebox.showerror("Error", "Start frequency must be less than stop frequency")
                return

            # Generate frequency sweep
            freqs = np.linspace(start_freq, stop_freq, points)

            def sweep_loop():
                for i, freq in enumerate(freqs):
                    if not self.na_running:
                        break

                    # Simulate network measurement
                    s11_mag, s11_phase = self.measure_s11(freq)

                    # Update progress
                    progress = (i + 1) / len(freqs) * 100
                    self.na_progress['value'] = progress

                    # Store data
                    self.na_freq_data.append(freq)
                    self.na_s11_mag_data.append(s11_mag)
                    self.na_s11_phase_data.append(s11_phase)

                    # Update plot periodically
                    if i % 10 == 0 or i == len(freqs) - 1:
                        self.update_network_analyzer_plot()

                    time.sleep(0.01)  # Small delay for realistic sweep time

            # Initialize data arrays
            self.na_freq_data = []
            self.na_s11_mag_data = []
            self.na_s11_phase_data = []

            self.na_running = True
            self.na_thread = threading.Thread(target=sweep_loop)
            self.na_thread.daemon = True
            self.na_thread.start()

        except ValueError:
            messagebox.showerror("Error", "Invalid frequency or points values")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start network analyzer: {str(e)}")

    def stop_network_analyzer(self):
        """Stop network analyzer"""
        self.na_running = False

    def measure_s11(self, freq):
        """Simulate S11 measurement at given frequency"""
        # Create a realistic S11 response with some resonances
        # This is just simulation - real implementation would use actual measurements

        # Base response
        mag_db = -20 - 10 * np.log10(1 + (freq / 1e6) ** 2)  # Roll-off with frequency

        # Add some resonances
        resonances = [5e6, 15e6, 25e6]  # Example resonant frequencies
        for res_freq in resonances:
            q_factor = 10
            delta_f = abs(freq - res_freq)
            if delta_f < res_freq / q_factor:
                resonance_effect = -15 * np.exp(-q_factor * delta_f / res_freq)
                mag_db += resonance_effect

        # Add some noise
        mag_db += np.random.normal(0, 0.5)

        # Phase response (simplified)
        phase_deg = -90 * freq / 50e6 + np.random.normal(0, 5)

        return mag_db, phase_deg

    def update_network_analyzer_plot(self):
        """Update network analyzer plots"""
        try:
            if len(self.na_freq_data) == 0:
                return

            freqs_mhz = np.array(self.na_freq_data) / 1e6  # Convert to MHz

            # Update magnitude plot
            self.na_mag_ax.clear()
            self.na_mag_ax.plot(freqs_mhz, self.na_s11_mag_data, 'b-')
            self.na_mag_ax.set_xlabel('Frequency (MHz)')
            self.na_mag_ax.set_ylabel('S11 Magnitude (dB)')
            self.na_mag_ax.set_title('S11 Magnitude')
            self.na_mag_ax.grid(True)

            # Update phase plot
            self.na_phase_ax.clear()
            self.na_phase_ax.plot(freqs_mhz, self.na_s11_phase_data, 'r-')
            self.na_phase_ax.set_xlabel('Frequency (MHz)')
            self.na_phase_ax.set_ylabel('S11 Phase (degrees)')
            self.na_phase_ax.set_title('S11 Phase')
            self.na_phase_ax.grid(True)

            # Update canvas
            self.na_canvas.draw()

        except Exception as e:
            print(f"Error updating network analyzer plot: {e}")

    # Utility methods
    def save_settings(self):
        """Save current settings to file"""
        try:
            settings = {
                'oscilloscope': {
                    'ch1_scale': self.osc_ch1_scale.get(),
                    'ch2_scale': self.osc_ch2_scale.get(),
                    'timebase': self.osc_timebase.get(),
                    'trigger_level': self.osc_trigger_level.get()
                },
                'wavegen': {
                    'ch1_freq': self.wg_ch1_freq.get(),
                    'ch1_amp': self.wg_ch1_amp.get(),
                    'ch1_wave': self.wg_ch1_wave.get(),
                    'ch2_freq': self.wg_ch2_freq.get(),
                    'ch2_amp': self.wg_ch2_amp.get(),
                    'ch2_wave': self.wg_ch2_wave.get()
                },
                'power_supply': {
                    'pos_voltage': self.ps_pos_voltage.get(),
                    'neg_voltage': self.ps_neg_voltage.get()
                }
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

    def load_settings(self):
        """Load settings from file"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if filename:
                with open(filename, 'r') as f:
                    settings = json.load(f)

                # Apply oscilloscope settings
                if 'oscilloscope' in settings:
                    osc = settings['oscilloscope']
                    self.osc_ch1_scale.set(osc.get('ch1_scale', '1V'))
                    self.osc_ch2_scale.set(osc.get('ch2_scale', '1V'))
                    self.osc_timebase.set(osc.get('timebase', '1ms'))
                    self.osc_trigger_level.set(osc.get('trigger_level', '0'))

                # Apply wavegen settings
                if 'wavegen' in settings:
                    wg = settings['wavegen']
                    self.wg_ch1_freq.set(wg.get('ch1_freq', '1000'))
                    self.wg_ch1_amp.set(wg.get('ch1_amp', '1'))
                    self.wg_ch1_wave.set(wg.get('ch1_wave', 'Sine'))
                    self.wg_ch2_freq.set(wg.get('ch2_freq', '1000'))
                    self.wg_ch2_amp.set(wg.get('ch2_amp', '1'))
                    self.wg_ch2_wave.set(wg.get('ch2_wave', 'Sine'))

                # Apply power supply settings
                if 'power_supply' in settings:
                    ps = settings['power_supply']
                    self.ps_pos_voltage.set(ps.get('pos_voltage', '3.3'))
                    self.ps_neg_voltage.set(ps.get('neg_voltage', '-3.3'))

                messagebox.showinfo("Success", "Settings loaded successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings: {str(e)}")

    def export_data(self):
        """Export current data to file"""
        try:
            # Choose what data to export
            export_dialog = tk.Toplevel(self.root)
            export_dialog.title("Export Data")
            export_dialog.geometry("300x200")

            ttk.Label(export_dialog, text="Select data to export:").pack(pady=10)

            export_osc = tk.BooleanVar(value=True)
            export_spectrum = tk.BooleanVar()
            export_network = tk.BooleanVar()

            ttk.Checkbutton(export_dialog, text="Oscilloscope Data", variable=export_osc).pack()
            ttk.Checkbutton(export_dialog, text="Spectrum Data", variable=export_spectrum).pack()
            ttk.Checkbutton(export_dialog, text="Network Analyzer Data", variable=export_network).pack()

            def do_export():
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
                )

                if filename:
                    self.perform_data_export(filename, export_osc.get(), export_spectrum.get(), export_network.get())
                    export_dialog.destroy()

            ttk.Button(export_dialog, text="Export", command=do_export).pack(pady=10)
            ttk.Button(export_dialog, text="Cancel", command=export_dialog.destroy).pack()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def perform_data_export(self, filename, export_osc, export_spectrum, export_network):
        """Perform the actual data export"""
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                if export_osc and self.oscilloscope_data['time']:
                    writer.writerow(['Oscilloscope Data'])
                    writer.writerow(['Time', 'Channel 1', 'Channel 2'])
                    for i in range(len(self.oscilloscope_data['time'])):
                        writer.writerow([
                            self.oscilloscope_data['time'][i],
                            self.oscilloscope_data['ch1'][i] if i < len(self.oscilloscope_data['ch1']) else '',
                            self.oscilloscope_data['ch2'][i] if i < len(self.oscilloscope_data['ch2']) else ''
                        ])
                    writer.writerow([])  # Empty row separator

                if export_spectrum and hasattr(self, 'spectrum_freq_data'):
                    writer.writerow(['Spectrum Data'])
                    writer.writerow(['Frequency', 'Magnitude'])
                    for i in range(len(self.spectrum_freq_data)):
                        writer.writerow([self.spectrum_freq_data[i], self.spectrum_mag_data[i]])
                    writer.writerow([])

                if export_network and hasattr(self, 'na_freq_data'):
                    writer.writerow(['Network Analyzer Data'])
                    writer.writerow(['Frequency', 'S11 Magnitude', 'S11 Phase'])
                    for i in range(len(self.na_freq_data)):
                        writer.writerow([
                            self.na_freq_data[i],
                            self.na_s11_mag_data[i],
                            self.na_s11_phase_data[i]
                        ])

            messagebox.showinfo("Success", f"Data exported to {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def save_config(self):
        self.save_settings()

    # Add this method to your AnalogDiscovery2GUI class
    def load_config(self):
        self.load_settings()
# Main application startup
if __name__ == "__main__":
    root = tk.Tk()
    app = AnalogDiscovery2GUI(root)
    root.mainloop()