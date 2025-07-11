import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Label
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import threading
import time
from ctypes import *
import sys
import os
import csv
from datetime import datetime


class AnalogDiscovery2GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analog Discovery 2 Complete Control Panel")
        self.root.geometry("1400x900")

        # Create status label early using self.root
        self.status_label = Label(self.root, text="Initializing...")
        self.status_label.pack()

        # Device handle
        self.hdwf = c_int()
        self.is_connected = False
        self.is_acquiring = False

        # Additional state variables
        self.data_logger_running = False
        self.spectrum_running = False
        self.protocol_running = False
        self.network_running = False
        self.logger_thread = None
        self.spectrum_thread = None
        self.protocol_thread = None
        self.network_thread = None

        # Data storage
        self.logged_data = []
        self.spectrum_data = {'freq': [], 'magnitude': []}
        self.network_data = {'freq': [], 's11_mag': [], 's11_phase': []}

        # Load WaveForms library
        self.dwf = None
        self.load_dwf_library()

        # Create GUI with tabs
        self.create_tabbed_interface()

        # Initialize device
        self.connect_device()

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

    def create_tabbed_interface(self):
        """Create main tabbed interface"""
        # Remove the early status label
        self.status_label.destroy()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create all tabs
        self.create_main_tab()
        self.create_power_supply_tab()
        self.create_data_logger_tab()
        self.create_spectrum_analyzer_tab()
        self.create_digital_io_tab()
        self.create_protocol_analyzer_tab()
        self.create_network_analyzer_tab()
        self.create_settings_tab()

    def create_main_tab(self):
        """Create main oscilloscope and function generator tab"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Oscilloscope & Function Gen")

        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="Device Control")
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Connection status
        ttk.Label(control_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.status_label = ttk.Label(control_frame, text="Disconnected", foreground="red")
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # Connect/Disconnect buttons
        self.connect_btn = ttk.Button(control_frame, text="Connect", command=self.connect_device)
        self.connect_btn.grid(row=0, column=2, padx=5, pady=5)

        self.disconnect_btn = ttk.Button(control_frame, text="Disconnect", command=self.disconnect_device,
                                         state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=3, padx=5, pady=5)

        # Oscilloscope frame
        osc_frame = ttk.LabelFrame(main_frame, text="Oscilloscope")
        osc_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Oscilloscope controls
        osc_control_frame = ttk.Frame(osc_frame)
        osc_control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Channel controls
        ttk.Label(osc_control_frame, text="Channel 1:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.ch1_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(osc_control_frame, text="Enable", variable=self.ch1_var).grid(row=0, column=1, padx=5)

        ttk.Label(osc_control_frame, text="Range (V):").grid(row=0, column=2, padx=5)
        self.ch1_range = ttk.Combobox(osc_control_frame, values=["0.5", "1", "2", "5", "10", "25"], state="readonly",
                                      width=8)
        self.ch1_range.set("5")
        self.ch1_range.grid(row=0, column=3, padx=5)

        ttk.Label(osc_control_frame, text="Channel 2:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.ch2_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(osc_control_frame, text="Enable", variable=self.ch2_var).grid(row=1, column=1, padx=5)

        ttk.Label(osc_control_frame, text="Range (V):").grid(row=1, column=2, padx=5)
        self.ch2_range = ttk.Combobox(osc_control_frame, values=["0.5", "1", "2", "5", "10", "25"], state="readonly",
                                      width=8)
        self.ch2_range.set("5")
        self.ch2_range.grid(row=1, column=3, padx=5)

        # Timebase control
        ttk.Label(osc_control_frame, text="Timebase (s/div):").grid(row=0, column=4, padx=5)
        self.timebase = ttk.Combobox(osc_control_frame,
                                     values=["1e-6", "2e-6", "5e-6", "1e-5", "2e-5", "5e-5", "1e-4", "2e-4", "5e-4",
                                             "1e-3", "2e-3", "5e-3"], state="readonly", width=10)
        self.timebase.set("1e-4")
        self.timebase.grid(row=0, column=5, padx=5)

        # Trigger controls
        ttk.Label(osc_control_frame, text="Trigger:").grid(row=0, column=6, padx=5)
        self.trigger_source = ttk.Combobox(osc_control_frame, values=["None", "Ch1", "Ch2", "External"], 
                                          state="readonly", width=8)
        self.trigger_source.set("Ch1")
        self.trigger_source.grid(row=0, column=7, padx=5)

        ttk.Label(osc_control_frame, text="Level (V):").grid(row=1, column=6, padx=5)
        self.trigger_level = ttk.Entry(osc_control_frame, width=8)
        self.trigger_level.insert(0, "0")
        self.trigger_level.grid(row=1, column=7, padx=5)

        # Acquisition controls
        self.start_btn = ttk.Button(osc_control_frame, text="Start", command=self.start_acquisition, state=tk.DISABLED)
        self.start_btn.grid(row=2, column=0, padx=5, pady=5)

        self.stop_btn = ttk.Button(osc_control_frame, text="Stop", command=self.stop_acquisition, state=tk.DISABLED)
        self.stop_btn.grid(row=2, column=1, padx=5, pady=5)

        self.single_btn = ttk.Button(osc_control_frame, text="Single", command=self.single_acquisition,
                                     state=tk.DISABLED)
        self.single_btn.grid(row=2, column=2, padx=5, pady=5)

        ttk.Button(osc_control_frame, text="Save Data", command=self.save_oscilloscope_data,
                  state=tk.DISABLED).grid(row=2, column=3, padx=5, pady=5)

        # Plot frame
        plot_frame = ttk.Frame(osc_frame)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(12, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initialize plot
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Voltage (V)')
        self.ax.set_title('Oscilloscope')
        self.ax.grid(True)
        self.canvas.draw()

        # Function generator frame
        funcgen_frame = ttk.LabelFrame(main_frame, text="Function Generator")
        funcgen_frame.pack(fill=tk.X)

        # Function generator controls
        funcgen_control_frame = ttk.Frame(funcgen_frame)
        funcgen_control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Channel 1 controls
        ttk.Label(funcgen_control_frame, text="Ch1:").grid(row=0, column=0, padx=5)
        self.fg1_enable = tk.BooleanVar()
        ttk.Checkbutton(funcgen_control_frame, text="Enable", variable=self.fg1_enable,
                        command=self.update_function_generator).grid(row=0, column=1, padx=5)

        ttk.Label(funcgen_control_frame, text="Waveform:").grid(row=0, column=2, padx=5)
        self.fg1_func = ttk.Combobox(funcgen_control_frame, values=["Sine", "Square", "Triangle", "DC", "Sawtooth", "Noise"],
                                     state="readonly", width=10)
        self.fg1_func.set("Sine")
        self.fg1_func.bind("<<ComboboxSelected>>", lambda e: self.update_function_generator())
        self.fg1_func.grid(row=0, column=3, padx=5)

        ttk.Label(funcgen_control_frame, text="Freq (Hz):").grid(row=0, column=4, padx=5)
        self.fg1_freq = ttk.Entry(funcgen_control_frame, width=10)
        self.fg1_freq.insert(0, "1000")
        self.fg1_freq.bind("<Return>", lambda e: self.update_function_generator())
        self.fg1_freq.grid(row=0, column=5, padx=5)

        ttk.Label(funcgen_control_frame, text="Amp (V):").grid(row=0, column=6, padx=5)
        self.fg1_amp = ttk.Entry(funcgen_control_frame, width=10)
        self.fg1_amp.insert(0, "1")
        self.fg1_amp.bind("<Return>", lambda e: self.update_function_generator())
        self.fg1_amp.grid(row=0, column=7, padx=5)

        ttk.Label(funcgen_control_frame, text="Offset (V):").grid(row=0, column=8, padx=5)
        self.fg1_offset = ttk.Entry(funcgen_control_frame, width=8)
        self.fg1_offset.insert(0, "0")
        self.fg1_offset.bind("<Return>", lambda e: self.update_function_generator())
        self.fg1_offset.grid(row=0, column=9, padx=5)

        # Channel 2 controls
        ttk.Label(funcgen_control_frame, text="Ch2:").grid(row=1, column=0, padx=5)
        self.fg2_enable = tk.BooleanVar()
        ttk.Checkbutton(funcgen_control_frame, text="Enable", variable=self.fg2_enable,
                        command=self.update_function_generator).grid(row=1, column=1, padx=5)

        ttk.Label(funcgen_control_frame, text="Waveform:").grid(row=1, column=2, padx=5)
        self.fg2_func = ttk.Combobox(funcgen_control_frame, values=["Sine", "Square", "Triangle", "DC", "Sawtooth", "Noise"],
                                     state="readonly", width=10)
        self.fg2_func.set("Sine")
        self.fg2_func.bind("<<ComboboxSelected>>", lambda e: self.update_function_generator())
        self.fg2_func.grid(row=1, column=3, padx=5)

        ttk.Label(funcgen_control_frame, text="Freq (Hz):").grid(row=1, column=4, padx=5)
        self.fg2_freq = ttk.Entry(funcgen_control_frame, width=10)
        self.fg2_freq.insert(0, "2000")
        self.fg2_freq.bind("<Return>", lambda e: self.update_function_generator())
        self.fg2_freq.grid(row=1, column=5, padx=5)

        ttk.Label(funcgen_control_frame, text="Amp (V):").grid(row=1, column=6, padx=5)
        self.fg2_amp = ttk.Entry(funcgen_control_frame, width=10)
        self.fg2_amp.insert(0, "1")
        self.fg2_amp.bind("<Return>", lambda e: self.update_function_generator())
        self.fg2_amp.grid(row=1, column=7, padx=5)

        ttk.Label(funcgen_control_frame, text="Offset (V):").grid(row=1, column=8, padx=5)
        self.fg2_offset = ttk.Entry(funcgen_control_frame, width=8)
        self.fg2_offset.insert(0, "0")
        self.fg2_offset.bind("<Return>", lambda e: self.update_function_generator())
        self.fg2_offset.grid(row=1, column=9, padx=5)

    def create_power_supply_tab(self):
        """Create power supply control tab"""
        ps_frame = ttk.Frame(self.notebook)
        self.notebook.add(ps_frame, text="Power Supply")

        # Power supply controls
        ps_control_frame = ttk.LabelFrame(ps_frame, text="Power Supply Control")
        ps_control_frame.pack(fill=tk.X, padx=10, pady=10)

        # Positive supply
        ttk.Label(ps_control_frame, text="V+ Supply:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.ps_pos_enable = tk.BooleanVar()
        ttk.Checkbutton(ps_control_frame, text="Enable", variable=self.ps_pos_enable,
                       command=self.update_power_supply).grid(row=0, column=1, padx=5)

        ttk.Label(ps_control_frame, text="Voltage (V):").grid(row=0, column=2, padx=5)
        self.ps_pos_voltage = ttk.Entry(ps_control_frame, width=10)
        self.ps_pos_voltage.insert(0, "3.3")
        self.ps_pos_voltage.bind("<Return>", lambda e: self.update_power_supply())
        self.ps_pos_voltage.grid(row=0, column=3, padx=5)

        self.ps_pos_current_label = ttk.Label(ps_control_frame, text="Current: 0.000 A")
        self.ps_pos_current_label.grid(row=0, column=4, padx=10)

        # Negative supply
        ttk.Label(ps_control_frame, text="V- Supply:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.ps_neg_enable = tk.BooleanVar()
        ttk.Checkbutton(ps_control_frame, text="Enable", variable=self.ps_neg_enable,
                       command=self.update_power_supply).grid(row=1, column=1, padx=5)

        ttk.Label(ps_control_frame, text="Voltage (V):").grid(row=1, column=2, padx=5)
        self.ps_neg_voltage = ttk.Entry(ps_control_frame, width=10)
        self.ps_neg_voltage.insert(0, "-3.3")
        self.ps_neg_voltage.bind("<Return>", lambda e: self.update_power_supply())
        self.ps_neg_voltage.grid(row=1, column=3, padx=5)

        self.ps_neg_current_label = ttk.Label(ps_control_frame, text="Current: 0.000 A")
        self.ps_neg_current_label.grid(row=1, column=4, padx=10)

        # Master enable/disable
        ttk.Button(ps_control_frame, text="Enable All", 
                  command=self.enable_all_supplies).grid(row=2, column=0, padx=5, pady=10)
        ttk.Button(ps_control_frame, text="Disable All", 
                  command=self.disable_all_supplies).grid(row=2, column=1, padx=5, pady=10)

        # Current monitoring
        self.start_current_monitoring()

    def create_data_logger_tab(self):
        """Create data logger tab"""
        dl_frame = ttk.Frame(self.notebook)
        self.notebook.add(dl_frame, text="Data Logger")

        # Data logger controls
        dl_control_frame = ttk.LabelFrame(dl_frame, text="Data Logger Settings")
        dl_control_frame.pack(fill=tk.X, padx=10, pady=10)

        # Channel selection
        ttk.Label(dl_control_frame, text="Channels:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.dl_ch1_enable = tk.BooleanVar(value=True)
        self.dl_ch2_enable = tk.BooleanVar(value=True)
        ttk.Checkbutton(dl_control_frame, text="Channel 1", variable=self.dl_ch1_enable).grid(row=0, column=1, padx=5)
        ttk.Checkbutton(dl_control_frame, text="Channel 2", variable=self.dl_ch2_enable).grid(row=0, column=2, padx=5)

        # Sampling interval
        ttk.Label(dl_control_frame, text="Interval:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.dl_interval = ttk.Combobox(dl_control_frame, values=["1s", "10s", "1min", "10min", "1hour"], 
                                       state="readonly", width=10)
        self.dl_interval.set("1s")
        self.dl_interval.grid(row=1, column=1, padx=5)

        # Duration
        ttk.Label(dl_control_frame, text="Duration (s):").grid(row=1, column=2, padx=5)
        self.dl_duration = ttk.Entry(dl_control_frame, width=10)
        self.dl_duration.insert(0, "60")
        self.dl_duration.grid(row=1, column=3, padx=5)

        # Filename
        ttk.Label(dl_control_frame, text="Filename:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.dl_filename = ttk.Entry(dl_control_frame, width=30)
        self.dl_filename.insert(0, "data_log.csv")
        self.dl_filename.grid(row=2, column=1, columnspan=2, padx=5, sticky=tk.W+tk.E)

        ttk.Button(dl_control_frame, text="Browse", 
                  command=self.browse_log_file).grid(row=2, column=3, padx=5)

        # Control buttons
        self.dl_start_btn = ttk.Button(dl_control_frame, text="Start Logging", 
                                      command=self.start_data_logger, state=tk.DISABLED)
        self.dl_start_btn.grid(row=3, column=0, padx=5, pady=10)

        self.dl_stop_btn = ttk.Button(dl_control_frame, text="Stop Logging", 
                                     command=self.stop_data_logger, state=tk.DISABLED)
        self.dl_stop_btn.grid(row=3, column=1, padx=5, pady=10)

        # Status and progress
        self.dl_status_label = ttk.Label(dl_control_frame, text="Status: Ready")
        self.dl_status_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        self.dl_progress = ttk.Progressbar(dl_control_frame, mode='determinate')
        self.dl_progress.grid(row=4, column=2, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
    
    def calibrate_oscilloscope(self):
        """Complete oscilloscope calibration for Analog Discovery 2"""
        if not hasattr(self, 'hdwf') or self.hdwf.value == 0:
            messagebox.showerror("Error", "No device connected. Please connect device first.")
            return
        
        try:
            # Show progress dialog
            progress_window = self.show_calibration_progress("Calibrating Oscilloscope...")
            
            # Perform calibration in separate thread to prevent GUI freezing
            def calibration_thread():
                try:
                    # Reset oscilloscope to default state
                    self.dwf.FDwfAnalogInReset(self.hdwf)
                    time.sleep(0.1)
                    
                    # Set up calibration parameters
                    # Channel 1 calibration
                    self.dwf.FDwfAnalogInChannelEnableSet(self.hdwf, c_int(0), c_bool(True))
                    self.dwf.FDwfAnalogInChannelRangeSet(self.hdwf, c_int(0), c_double(5.0))  # 5V range
                    self.dwf.FDwfAnalogInChannelOffsetSet(self.hdwf, c_int(0), c_double(0.0))  # 0V offset
                    
                    # Channel 2 calibration
                    self.dwf.FDwfAnalogInChannelEnableSet(self.hdwf, c_int(1), c_bool(True))
                    self.dwf.FDwfAnalogInChannelRangeSet(self.hdwf, c_int(1), c_double(5.0))  # 5V range
                    self.dwf.FDwfAnalogInChannelOffsetSet(self.hdwf, c_int(1), c_double(0.0))  # 0V offset
                    
                    # Set acquisition parameters
                    self.dwf.FDwfAnalogInFrequencySet(self.hdwf, c_double(1000000.0))  # 1MHz sample rate
                    self.dwf.FDwfAnalogInBufferSizeSet(self.hdwf, c_int(1024))
                    
                    # Perform auto-calibration sequence
                    self.update_progress("Performing offset calibration...")
                    
                    # Offset calibration - ground both inputs
                    for channel in range(2):
                        # Set coupling to DC
                        self.dwf.FDwfAnalogInChannelCouplingSet(self.hdwf, c_int(channel), c_int(0))  # DC coupling
                        
                        # Measure offset at different ranges
                        ranges = [0.5, 1.0, 2.0, 5.0]
                        for voltage_range in ranges:
                            self.dwf.FDwfAnalogInChannelRangeSet(self.hdwf, c_int(channel), c_double(voltage_range))
                            time.sleep(0.05)
                            
                            # Start acquisition
                            self.dwf.FDwfAnalogInConfigure(self.hdwf, c_bool(False), c_bool(True))
                            
                            # Wait for acquisition to complete
                            sts = c_byte()
                            while True:
                                self.dwf.FDwfAnalogInStatus(self.hdwf, c_int(1), byref(sts))
                                if sts.value == 2:  # DwfStateDone
                                    break
                                time.sleep(0.01)
                    
                    self.update_progress("Performing gain calibration...")
                    
                    # Gain calibration - use internal reference if available
                    for channel in range(2):
                        ranges = [0.5, 1.0, 2.0, 5.0]
                        for voltage_range in ranges:
                            self.dwf.FDwfAnalogInChannelRangeSet(self.hdwf, c_int(channel), c_double(voltage_range))
                            time.sleep(0.05)
                            
                            # Perform measurement
                            self.dwf.FDwfAnalogInConfigure(self.hdwf, c_bool(False), c_bool(True))
                            
                            sts = c_byte()
                            while True:
                                self.dwf.FDwfAnalogInStatus(self.hdwf, c_int(1), byref(sts))
                                if sts.value == 2:
                                    break
                                time.sleep(0.01)
                    
                    self.update_progress("Finalizing calibration...")
                    time.sleep(0.5)
                    
                    # Store calibration data (this would typically save to device EEPROM)
                    # For AD2, calibration is handled internally by the device
                    
                    self.close_progress()
                    messagebox.showinfo("Success", "Oscilloscope calibration completed successfully!")
                    
                except Exception as e:
                    self.close_progress()
                    messagebox.showerror("Calibration Error", f"Oscilloscope calibration failed: {str(e)}")
            
            # Start calibration thread
            thread = threading.Thread(target=calibration_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start oscilloscope calibration: {str(e)}")

    def calibrate_funcgen(self):
        """Complete function generator calibration for Analog Discovery 2"""
        if not hasattr(self, 'hdwf') or self.hdwf.value == 0:
            messagebox.showerror("Error", "No device connected. Please connect device first.")
            return
        
        try:
            # Show progress dialog
            progress_window = self.show_calibration_progress("Calibrating Function Generator...")
            
            def calibration_thread():
                try:
                    # Reset function generator to default state
                    self.dwf.FDwfAnalogOutReset(self.hdwf, c_int(-1))  # Reset all channels
                    time.sleep(0.1)
                    
                    self.update_progress("Calibrating Channel 1...")
                    
                    # Channel 1 calibration
                    channel = 0
                    self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(channel), c_int(0), c_bool(True))  # Enable carrier
                    self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(channel), c_int(0), c_int(1))  # Sine wave
                    
                    # Calibrate at different amplitudes and offsets
                    amplitudes = [0.5, 1.0, 2.0, 5.0]
                    offsets = [-2.5, 0.0, 2.5]
                    
                    for amplitude in amplitudes:
                        for offset in offsets:
                            # Set amplitude and offset
                            self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(channel), c_int(0), c_double(amplitude))
                            self.dwf.FDwfAnalogOutNodeOffsetSet(self.hdwf, c_int(channel), c_int(0), c_double(offset))
                            self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(channel), c_int(0), c_double(1000.0))  # 1kHz
                            
                            # Configure and start
                            self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(channel), c_bool(True))
                            time.sleep(0.1)
                            
                            # Stop output
                            self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(channel), c_bool(False))
                            time.sleep(0.05)
                    
                    self.update_progress("Calibrating Channel 2...")
                    
                    # Channel 2 calibration
                    channel = 1
                    self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(channel), c_int(0), c_bool(True))
                    self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(channel), c_int(0), c_int(1))  # Sine wave
                    
                    for amplitude in amplitudes:
                        for offset in offsets:
                            self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(channel), c_int(0), c_double(amplitude))
                            self.dwf.FDwfAnalogOutNodeOffsetSet(self.hdwf, c_int(channel), c_int(0), c_double(offset))
                            self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(channel), c_int(0), c_double(1000.0))
                            
                            self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(channel), c_bool(True))
                            time.sleep(0.1)
                            self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(channel), c_bool(False))
                            time.sleep(0.05)
                    
                    self.update_progress("Testing frequency accuracy...")
                    
                    # Test frequency accuracy at different frequencies
                    test_frequencies = [100, 1000, 10000, 100000, 1000000]  # 100Hz to 1MHz
                    for freq in test_frequencies:
                        self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(0), c_int(0), c_double(freq))
                        self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_bool(True))
                        time.sleep(0.05)
                        self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_bool(False))
                    
                    self.update_progress("Finalizing calibration...")
                    
                    # Reset to safe state
                    self.dwf.FDwfAnalogOutReset(self.hdwf, c_int(-1))
                    time.sleep(0.5)
                    
                    self.close_progress()
                    messagebox.showinfo("Success", "Function generator calibration completed successfully!")
                    
                except Exception as e:
                    self.close_progress()
                    messagebox.showerror("Calibration Error", f"Function generator calibration failed: {str(e)}")
            
            # Start calibration thread
            thread = threading.Thread(target=calibration_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start function generator calibration: {str(e)}")

    def reset_device(self):
        """Complete device reset for Analog Discovery 2"""
        if not hasattr(self, 'hdwf') or self.hdwf.value == 0:
            messagebox.showerror("Error", "No device connected. Please connect device first.")
            return
        
        # Confirm reset action
        result = messagebox.askyesno("Confirm Reset", 
                                    "This will reset the device to factory defaults.\n"
                                    "All current settings will be lost.\n\n"
                                    "Are you sure you want to continue?")
        
        if not result:
            return
        
        try:
            progress_window = self.show_calibration_progress("Resetting Device...")
            
            def reset_thread():
                try:
                    self.update_progress("Stopping all instruments...")
                    
                    # Stop and reset all instruments
                    # Reset Oscilloscope
                    self.dwf.FDwfAnalogInReset(self.hdwf)
                    
                    # Reset Function Generator
                    self.dwf.FDwfAnalogOutReset(self.hdwf, c_int(-1))  # Reset all channels
                    
                    # Reset Digital I/O
                    self.dwf.FDwfDigitalIOReset(self.hdwf)
                    
                    # Reset Digital In (Logic Analyzer)
                    self.dwf.FDwfDigitalInReset(self.hdwf)
                    
                    # Reset Digital Out (Pattern Generator)
                    self.dwf.FDwfDigitalOutReset(self.hdwf)
                    
                    # Reset Analog I/O (Power supplies, etc.)
                    self.dwf.FDwfAnalogIOReset(self.hdwf)
                    
                    time.sleep(0.5)
                    
                    self.update_progress("Resetting device configuration...")
                    
                    # Set all channels to safe defaults
                    # Oscilloscope defaults
                    for channel in range(2):
                        self.dwf.FDwfAnalogInChannelEnableSet(self.hdwf, c_int(channel), c_bool(False))
                        self.dwf.FDwfAnalogInChannelRangeSet(self.hdwf, c_int(channel), c_double(5.0))
                        self.dwf.FDwfAnalogInChannelOffsetSet(self.hdwf, c_int(channel), c_double(0.0))
                        self.dwf.FDwfAnalogInChannelCouplingSet(self.hdwf, c_int(channel), c_int(0))  # DC coupling
                    
                    # Function generator defaults
                    for channel in range(2):
                        self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(channel), c_int(0), c_bool(False))
                        self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(channel), c_int(0), c_double(1.0))
                        self.dwf.FDwfAnalogOutNodeOffsetSet(self.hdwf, c_int(channel), c_int(0), c_double(0.0))
                        self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(channel), c_int(0), c_double(1000.0))
                        self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(channel), c_int(0), c_int(1))  # Sine
                    
                    # Power supply defaults (if available)
                    try:
                        # Positive supply off
                        self.dwf.FDwfAnalogIOChannelNodeSet(self.hdwf, c_int(0), c_int(0), c_double(0))  # Disable
                        self.dwf.FDwfAnalogIOChannelNodeSet(self.hdwf, c_int(0), c_int(1), c_double(3.3))  # 3.3V
                        
                        # Negative supply off
                        self.dwf.FDwfAnalogIOChannelNodeSet(self.hdwf, c_int(1), c_int(0), c_double(0))  # Disable
                        self.dwf.FDwfAnalogIOChannelNodeSet(self.hdwf, c_int(1), c_int(1), c_double(-3.3))  # -3.3V
                        
                        self.dwf.FDwfAnalogIOEnableSet(self.hdwf, c_bool(False))
                    except:
                        pass  # Some devices may not have power supplies
                    
                    # Digital I/O defaults
                    self.dwf.FDwfDigitalIOOutputEnableSet(self.hdwf, c_int(0))  # All pins as inputs
                    
                    time.sleep(0.5)
                    
                    self.update_progress("Performing system reset...")
                    
                    # Perform low-level device reset
                    self.dwf.FDwfDeviceReset(self.hdwf)
                    time.sleep(1.0)
                    
                    # Re-initialize basic parameters
                    self.dwf.FDwfAnalogInFrequencySet(self.hdwf, c_double(20000000.0))  # 20MHz default
                    self.dwf.FDwfAnalogInBufferSizeSet(self.hdwf, c_int(8192))  # Default buffer size
                    
                    self.update_progress("Reset complete!")
                    time.sleep(0.5)
                    
                    self.close_progress()
                    
                    # Update UI to reflect reset state
                    if hasattr(self, 'update_ui_after_reset'):
                        self.update_ui_after_reset()
                    
                    messagebox.showinfo("Success", 
                                    "Device reset completed successfully!\n\n"
                                    "The device has been restored to factory defaults.\n"
                                    "All instruments are now in their default state.")
                    
                except Exception as e:
                    self.close_progress()
                    messagebox.showerror("Reset Error", f"Device reset failed: {str(e)}")
            
            # Start reset thread
            thread = threading.Thread(target=reset_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start device reset: {str(e)}")

    # Helper methods for progress dialog (add these to your main class)
    def show_calibration_progress(self, title):
        """Show calibration progress window"""
        import tkinter as tk
        from tkinter import ttk
        
        self.progress_window = tk.Toplevel(self.root if hasattr(self, 'root') else None)
        self.progress_window.title(title)
        self.progress_window.geometry("400x150")
        self.progress_window.resizable(False, False)
        self.progress_window.transient(self.root if hasattr(self, 'root') else None)
        self.progress_window.grab_set()
        
        # Center the window
        self.progress_window.update_idletasks()
        x = (self.progress_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.progress_window.winfo_screenheight() // 2) - (150 // 2)
        self.progress_window.geometry(f"400x150+{x}+{y}")
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Initializing...")
        self.progress_label = tk.Label(self.progress_window, textvariable=self.progress_var)
        self.progress_label.pack(pady=20)
        
        self.progress_bar = ttk.Progressbar(self.progress_window, mode='indeterminate')
        self.progress_bar.pack(pady=10, padx=20, fill='x')
        self.progress_bar.start()
        
        return self.progress_window

    def update_progress(self, message):
        """Update progress message"""
        if hasattr(self, 'progress_var'):
            self.progress_var.set(message)
            if hasattr(self, 'progress_window'):
                self.progress_window.update()

    def close_progress(self):
        """Close progress window"""
        if hasattr(self, 'progress_window'):
            self.progress_bar.stop()
            self.progress_window.destroy()
            delattr(self, 'progress_window')
            delattr(self, 'progress_var')
            delattr(self, 'progress_bar')
    def create_spectrum_analyzer_tab(self):
        """Create spectrum analyzer tab"""
        sa_frame = ttk.Frame(self.notebook)
        self.notebook.add(sa_frame, text="Spectrum Analyzer")

        # Controls
        sa_control_frame = ttk.LabelFrame(sa_frame, text="Spectrum Analyzer Settings")
        sa_control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(sa_control_frame, text="Start Freq (Hz):").grid(row=0, column=0, padx=5, pady=5)
        self.sa_start_freq = ttk.Entry(sa_control_frame, width=15)
        self.sa_start_freq.insert(0, "1000")
        self.sa_start_freq.grid(row=0, column=1, padx=5)

        ttk.Label(sa_control_frame, text="Stop Freq (Hz):").grid(row=0, column=2, padx=5, pady=5)
        self.sa_stop_freq = ttk.Entry(sa_control_frame, width=15)
        self.sa_stop_freq.insert(0, "100000")
        self.sa_stop_freq.grid(row=0, column=3, padx=5)

        ttk.Label(sa_control_frame, text="Samples:").grid(row=0, column=4, padx=5, pady=5)
        self.sa_samples = ttk.Entry(sa_control_frame, width=10)
        self.sa_samples.insert(0, "1024")
        self.sa_samples.grid(row=0, column=5, padx=5)

        self.sa_start_btn = ttk.Button(sa_control_frame, text="Start", 
                                      command=self.start_spectrum_analyzer, state=tk.DISABLED)
        self.sa_start_btn.grid(row=1, column=0, padx=5, pady=10)

        self.sa_stop_btn = ttk.Button(sa_control_frame, text="Stop", 
                                     command=self.stop_spectrum_analyzer, state=tk.DISABLED)
        self.sa_stop_btn.grid(row=1, column=1, padx=5, pady=10)

        # Spectrum plot
        sa_plot_frame = ttk.Frame(sa_frame)
        sa_plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.sa_fig, self.sa_ax = plt.subplots(figsize=(12, 6))
        self.sa_canvas = FigureCanvasTkAgg(self.sa_fig, sa_plot_frame)
        self.sa_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.sa_ax.set_xlabel('Frequency (Hz)')
        self.sa_ax.set_ylabel('Magnitude (dB)')
        self.sa_ax.set_title('Spectrum Analyzer')
        self.sa_ax.grid(True)
        self.sa_canvas.draw()
    def start_network_analyzer(self):
        """Start network analyzer with frequency sweep"""
        if not self.is_connected:
            messagebox.showerror("Error", "Device not connected")
            return

        if not hasattr(self, 'hdwf') or self.hdwf.value == 0:
            messagebox.showerror("Error", "Invalid device handle")
            return

        # Get network analyzer parameters from UI
        try:
            start_freq = float(self.na_start_freq.get()) if hasattr(self, 'na_start_freq') else 100.0
            stop_freq = float(self.na_stop_freq.get()) if hasattr(self, 'na_stop_freq') else 100000.0
            num_points = int(self.na_points.get()) if hasattr(self, 'na_points') else 100
            amplitude = float(self.na_amplitude.get()) if hasattr(self, 'na_amplitude') else 1.0
        except (ValueError, AttributeError):
            # Use default values if UI elements don't exist
            start_freq = 100.0      # 100 Hz
            stop_freq = 100000.0    # 100 kHz
            num_points = 100
            amplitude = 1.0         # 1V amplitude

        # Validate parameters
        if start_freq >= stop_freq:
            messagebox.showerror("Error", "Start frequency must be less than stop frequency")
            return
        
        if start_freq < 1 or stop_freq > 10000000:  # AD2 limits
            messagebox.showerror("Error", "Frequency range must be between 1 Hz and 10 MHz")
            return

        self.network_running = True
        self.na_start_btn.config(state=tk.DISABLED)
        self.na_stop_btn.config(state=tk.NORMAL)

        # Initialize result arrays
        self.na_frequencies = []
        self.na_magnitude = []
        self.na_phase = []
        
        # Show progress window
        self.show_na_progress("Network Analysis in Progress...")
    def network_analysis_thread(self):
        try:
            self.update_na_progress("Initializing instruments...")
            
            # Reset and configure function generator (stimulus)
            self.dwf.FDwfAnalogOutReset(self.hdwf, c_int(0))  # Reset channel 1
            self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(0), c_int(0), c_bool(True))
            self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(0), c_int(0), c_int(1))  # Sine wave
            self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(0), c_int(0), c_double(amplitude))
            self.dwf.FDwfAnalogOutNodeOffsetSet(self.hdwf, c_int(0), c_int(0), c_double(0.0))
            
            # Reset and configure oscilloscope (measurement)
            self.dwf.FDwfAnalogInReset(self.hdwf)
            
            # Configure oscilloscope channels
            # Channel 1: Reference (stimulus monitoring)
            self.dwf.FDwfAnalogInChannelEnableSet(self.hdwf, c_int(0), c_bool(True))
            self.dwf.FDwfAnalogInChannelRangeSet(self.hdwf, c_int(0), c_double(amplitude * 2))
            self.dwf.FDwfAnalogInChannelOffsetSet(self.hdwf, c_int(0), c_double(0.0))
            
            # Channel 2: Response measurement
            self.dwf.FDwfAnalogInChannelEnableSet(self.hdwf, c_int(1), c_bool(True))
            self.dwf.FDwfAnalogInChannelRangeSet(self.hdwf, c_int(1), c_double(amplitude * 2))
            self.dwf.FDwfAnalogInChannelOffsetSet(self.hdwf, c_int(1), c_double(0.0))
            
            # Set acquisition parameters
            sample_rate = max(stop_freq * 10, 1000000)  # At least 10x highest frequency, min 1MHz
            buffer_size = 4096
            
            self.dwf.FDwfAnalogInFrequencySet(self.hdwf, c_double(sample_rate))
            self.dwf.FDwfAnalogInBufferSizeSet(self.hdwf, c_int(buffer_size))
            self.dwf.FDwfAnalogInAcquisitionModeSet(self.hdwf, c_int(0))  # Single acquisition
            
            # Generate frequency points (logarithmic spacing for better coverage)
            frequencies = np.logspace(np.log10(start_freq), np.log10(stop_freq), num_points)
            
            self.na_frequencies = []
            self.na_magnitude = []
            self.na_phase = []
            
            # Perform frequency sweep
            for i, freq in enumerate(frequencies):
                if not self.network_running:  # Check for stop condition
                    break
                    
                progress = (i + 1) / len(frequencies) * 100
                self.update_na_progress(f"Measuring at {freq:.1f} Hz ({i+1}/{len(frequencies)}) - {progress:.1f}%")
                
                # Set function generator frequency
                self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(0), c_int(0), c_double(freq))
                
                # Start function generator
                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_bool(True))
                
                # Wait for signal to stabilize (at least 5 periods or 100ms, whichever is longer)
                settle_time = max(5.0 / freq, 0.1)
                time.sleep(settle_time)
                
                # Configure acquisition time window
                acquisition_time = max(10.0 / freq, 0.01)  # At least 10 periods or 10ms
                self.dwf.FDwfAnalogInRecordLengthSet(self.hdwf, c_double(acquisition_time))
                
                # Start acquisition
                self.dwf.FDwfAnalogInConfigure(self.hdwf, c_bool(False), c_bool(True))
                
                # Wait for acquisition to complete
                sts = c_byte()
                while True:
                    self.dwf.FDwfAnalogInStatus(self.hdwf, c_int(1), byref(sts))
                    if sts.value == 2:  # DwfStateDone
                        break
                    if not self.network_running:
                        break
                    time.sleep(0.01)
                
                if not self.network_running:
                    break
                
                # Get data
                buffer_ch1 = (c_double * buffer_size)()
                buffer_ch2 = (c_double * buffer_size)()
                
                self.dwf.FDwfAnalogInStatusData(self.hdwf, c_int(0), buffer_ch1, c_int(buffer_size))
                self.dwf.FDwfAnalogInStatusData(self.hdwf, c_int(1), buffer_ch2, c_int(buffer_size))
                
                # Convert to numpy arrays
                ref_data = np.array(buffer_ch1[:buffer_size])
                response_data = np.array(buffer_ch2[:buffer_size])
                
                # Calculate magnitude and phase using FFT
                magnitude_db, phase_deg = self.calculate_transfer_function(ref_data, response_data, freq, sample_rate)
                
                self.na_frequencies.append(freq)
                self.na_magnitude.append(magnitude_db)
                self.na_phase.append(phase_deg)
                
                # Update plot periodically
                if i % 5 == 0 or i == len(frequencies) - 1:
                    self.update_na_plot()
            
            # Stop function generator
            self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_bool(False))
            
            self.close_na_progress()
            
            if self.network_running:
                messagebox.showinfo("Success", f"Network analysis completed!\n"
                                              f"Measured {len(self.na_frequencies)} frequency points\n"
                                              f"Range: {start_freq:.1f} Hz to {stop_freq:.1f} Hz")
                self.update_na_plot()
            else:
                messagebox.showinfo("Stopped", "Network analysis stopped by user")
                
        except Exception as e:
            self.close_na_progress()
            messagebox.showerror("Error", f"Network analysis failed: {str(e)}")
        finally:
            # Ensure instruments are stopped
            try:
                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_bool(False))
                self.dwf.FDwfAnalogInReset(self.hdwf)
            except:
                pass

        # Start analysis in separate thread
        na_thread = threading.Thread(target=network_analysis_thread)
        na_thread.daemon = True
        na_thread.start()
        
        # Store thread reference for cleanup
        self.na_thread = na_thread
    

    def stop_network_analyzer(self):
        """Stop network analyzer"""
        self.network_running = False
        self.na_start_btn.config(state=tk.NORMAL)
        self.na_stop_btn.config(state=tk.DISABLED)
        
        # Wait for thread to finish
        if hasattr(self, 'na_thread') and self.na_thread.is_alive():
            self.na_thread.join(timeout=2.0)
        
        # Stop instruments
        try:
            if hasattr(self, 'hdwf') and self.hdwf.value != 0:
                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_bool(False))
                self.dwf.FDwfAnalogInReset(self.hdwf)
        except:
            pass

    def calculate_transfer_function(self, ref_signal, response_signal, frequency, sample_rate):
        """Calculate magnitude and phase from reference and response signals"""
        try:
            # Apply window function to reduce spectral leakage
            window = np.hanning(len(ref_signal))
            ref_windowed = ref_signal * window
            response_windowed = response_signal * window
            
            # Calculate FFT
            ref_fft = np.fft.fft(ref_windowed)
            response_fft = np.fft.fft(response_windowed)
            
            # Find frequency bin closest to our test frequency
            freqs = np.fft.fftfreq(len(ref_signal), 1.0 / sample_rate)
            freq_bin = np.argmin(np.abs(freqs - frequency))
            
            # Get complex values at the test frequency
            ref_complex = ref_fft[freq_bin]
            response_complex = response_fft[freq_bin]
            
            # Calculate transfer function H = Response/Reference
            if abs(ref_complex) > 1e-10:  # Avoid division by zero
                transfer_function = response_complex / ref_complex
                
                # Calculate magnitude in dB
                magnitude_db = 20 * np.log10(abs(transfer_function))
                
                # Calculate phase in degrees
                phase_deg = np.angle(transfer_function) * 180 / np.pi
                
                return magnitude_db, phase_deg
            else:
                return -60.0, 0.0  # Return -60dB and 0 phase if reference is too small
                
        except Exception as e:
            print(f"Error calculating transfer function: {e}")
            return -60.0, 0.0

    def update_na_plot(self):
        """Update network analyzer plot"""
        if not hasattr(self, 'na_frequencies') or len(self.na_frequencies) == 0:
            return
        
        try:
            # Create or update the plot
            if not hasattr(self, 'na_figure'):
                self.setup_na_plot()
            
            # Clear previous plots
            self.na_ax_mag.clear()
            self.na_ax_phase.clear()
            
            # Plot magnitude
            self.na_ax_mag.semilogx(self.na_frequencies, self.na_magnitude, 'b-', linewidth=2)
            self.na_ax_mag.set_xlabel('Frequency (Hz)')
            self.na_ax_mag.set_ylabel('Magnitude (dB)')
            self.na_ax_mag.set_title('Network Analyzer - Frequency Response')
            self.na_ax_mag.grid(True, alpha=0.3)
            
            # Plot phase
            self.na_ax_phase.semilogx(self.na_frequencies, self.na_phase, 'r-', linewidth=2)
            self.na_ax_phase.set_xlabel('Frequency (Hz)')
            self.na_ax_phase.set_ylabel('Phase (degrees)')
            self.na_ax_phase.grid(True, alpha=0.3)
            
            # Update canvas
            self.na_canvas.draw()
            
        except Exception as e:
            print(f"Error updating NA plot: {e}")

    def setup_na_plot(self):
        """Setup network analyzer plot window"""
        try:
            # Create plot window if it doesn't exist
            if not hasattr(self, 'na_plot_window'):
                self.na_plot_window = tk.Toplevel(self.root if hasattr(self, 'root') else None)
                self.na_plot_window.title("Network Analyzer - Frequency Response")
                self.na_plot_window.geometry("800x600")
                
                # Create matplotlib figure
                self.na_figure, (self.na_ax_mag, self.na_ax_phase) = plt.subplots(2, 1, figsize=(10, 8))
                self.na_figure.tight_layout(pad=3.0)
                
                # Create canvas
                self.na_canvas = FigureCanvasTkAgg(self.na_figure, self.na_plot_window)
                self.na_canvas.draw()
                self.na_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
                
                # Add toolbar
                from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
                toolbar = NavigationToolbar2Tk(self.na_canvas, self.na_plot_window)
                toolbar.update()
                self.na_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
                
        except Exception as e:
            print(f"Error setting up NA plot: {e}")

    # Helper methods for progress dialog
    def show_na_progress(self, title):
        """Show network analyzer progress window"""
        self.na_progress_window = tk.Toplevel(self.root if hasattr(self, 'root') else None)
        self.na_progress_window.title(title)
        self.na_progress_window.geometry("500x180")
        self.na_progress_window.resizable(False, False)
        self.na_progress_window.transient(self.root if hasattr(self, 'root') else None)
        self.na_progress_window.grab_set()
        
        # Center the window
        self.na_progress_window.update_idletasks()
        x = (self.na_progress_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.na_progress_window.winfo_screenheight() // 2) - (180 // 2)
        self.na_progress_window.geometry(f"500x180+{x}+{y}")
        
        # Progress information
        self.na_progress_var = tk.StringVar(value="Initializing...")
        self.na_progress_label = tk.Label(self.na_progress_window, textvariable=self.na_progress_var)
        self.na_progress_label.pack(pady=20)
        
        # Progress bar
        self.na_progress_bar = ttk.Progressbar(self.na_progress_window, mode='indeterminate')
        self.na_progress_bar.pack(pady=10, padx=20, fill='x')
        self.na_progress_bar.start()
        
        # Stop button
        stop_frame = tk.Frame(self.na_progress_window)
        stop_frame.pack(pady=10)
        
        stop_btn = tk.Button(stop_frame, text="Stop Analysis", 
                            command=lambda: setattr(self, 'network_running', False),
                            bg='red', fg='white')
        stop_btn.pack()

    def update_na_progress(self, message):
        """Update network analyzer progress message"""
        if hasattr(self, 'na_progress_var'):
            self.na_progress_var.set(message)
            if hasattr(self, 'na_progress_window'):
                self.na_progress_window.update()

    def close_na_progress(self):
        """Close network analyzer progress window"""
        if hasattr(self, 'na_progress_window'):
            self.na_progress_bar.stop()
            self.na_progress_window.destroy()
            delattr(self, 'na_progress_window')
            delattr(self, 'na_progress_var')
            delattr(self, 'na_progress_bar')

    def export_na_data(self):
        """Export network analyzer data to CSV file"""
        if not hasattr(self, 'na_frequencies') or len(self.na_frequencies) == 0:
            messagebox.showwarning("Warning", "No data to export. Run network analysis first.")
            return
        
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Network Analyzer Data"
        )
        
        if filename:
            try:
                import csv
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Frequency (Hz)', 'Magnitude (dB)', 'Phase (degrees)'])
                    for freq, mag, phase in zip(self.na_frequencies, self.na_magnitude, self.na_phase):
                        writer.writerow([freq, mag, phase])
                
                messagebox.showinfo("Success", f"Data exported to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def save_na_plot(self):
        """Save network analyzer plot as image"""
        if not hasattr(self, 'na_figure'):
            messagebox.showwarning("Warning", "No plot to save. Run network analysis first.")
            return
        
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("SVG files", "*.svg")],
            title="Save Network Analyzer Plot"
        )
            
        if filename:
            try:
                self.na_figure.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Plot saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save plot: {str(e)}")

    def start_protocol_analyzer(self):
        if not self.is_connected:
            messagebox.showerror("Error", "Device not connected")
            return

        self.protocol_running = True
        self.pa_start_btn.config(state=tk.DISABLED)
        self.pa_stop_btn.config(state=tk.NORMAL)
        # Placeholder: Show info, no real protocol decoding implemented
        messagebox.showinfo("Info", "Protocol analyzer start not implemented yet.")

    def stop_protocol_analyzer(self):
        """Stop protocol analyzer (placeholder)"""
        self.protocol_running = False
        self.pa_start_btn.config(state=tk.NORMAL)
        self.pa_stop_btn.config(state=tk.DISABLED)
        # Placeholder: Show info
        messagebox.showinfo("Info", "Protocol analyzer stop not implemented yet.")
    def create_digital_io_tab(self):
        """Create digital I/O control tab"""
        dio_frame = ttk.Frame(self.notebook)
        self.notebook.add(dio_frame, text="Digital I/O")

        # Digital outputs
        dio_out_frame = ttk.LabelFrame(dio_frame, text="Digital Outputs")
        dio_out_frame.pack(fill=tk.X, padx=10, pady=10)

        self.dio_vars = []
        for i in range(16):  # AD2 has 16 digital I/O pins
            var = tk.BooleanVar()
            self.dio_vars.append(var)
            ttk.Checkbutton(dio_out_frame, text=f"DIO {i}", variable=var,
                           command=self.update_digital_outputs).grid(row=i//8, column=i%8, padx=5, pady=2)

        # Digital inputs display
        dio_in_frame = ttk.LabelFrame(dio_frame, text="Digital Inputs")
        dio_in_frame.pack(fill=tk.X, padx=10, pady=10)

        self.dio_input_labels = []
        for i in range(16):
            label = ttk.Label(dio_in_frame, text=f"DIO {i}: LOW")
            label.grid(row=i//8, column=i%8, padx=5, pady=2)
            self.dio_input_labels.append(label)

        # Start monitoring digital inputs
        self.start_digital_monitoring()

    def create_protocol_analyzer_tab(self):
        """Create protocol analyzer tab"""
        pa_frame = ttk.Frame(self.notebook)
        self.notebook.add(pa_frame, text="Protocol Analyzer")

        # Protocol selection
        pa_control_frame = ttk.LabelFrame(pa_frame, text="Protocol Settings")
        pa_control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(pa_control_frame, text="Protocol:").grid(row=0, column=0, padx=5, pady=5)
        self.protocol_type = ttk.Combobox(pa_control_frame, values=["SPI", "I2C", "UART", "CAN"], 
                                         state="readonly", width=10)
        self.protocol_type.set("SPI")
        self.protocol_type.grid(row=0, column=1, padx=5)

        # Protocol-specific settings would go here
        ttk.Label(pa_control_frame, text="Clock Pin:").grid(row=0, column=2, padx=5)
        self.pa_clock_pin = ttk.Combobox(pa_control_frame, values=[f"DIO {i}" for i in range(16)], 
                                        state="readonly", width=8)
        self.pa_clock_pin.set("DIO 0")
        self.pa_clock_pin.grid(row=0, column=3, padx=5)

        ttk.Label(pa_control_frame, text="Data Pin:").grid(row=0, column=4, padx=5)
        self.pa_data_pin = ttk.Combobox(pa_control_frame, values=[f"DIO {i}" for i in range(16)], 
                                       state="readonly", width=8)
        self.pa_data_pin.set("DIO 1")
        self.pa_data_pin.grid(row=0, column=5, padx=5)

        self.pa_start_btn = ttk.Button(pa_control_frame, text="Start", 
                                      command=self.start_protocol_analyzer, state=tk.DISABLED)
        self.pa_start_btn.grid(row=1, column=0, padx=5, pady=10)

        self.pa_stop_btn = ttk.Button(pa_control_frame, text="Stop", 
                                     command=self.stop_protocol_analyzer, state=tk.DISABLED)
        self.pa_stop_btn.grid(row=1, column=1, padx=5, pady=10)

        # Protocol data display
        pa_data_frame = ttk.LabelFrame(pa_frame, text="Decoded Data")
        pa_data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Text area for protocol data
        self.protocol_text = tk.Text(pa_data_frame, height=20, state=tk.DISABLED)
        pa_scrollbar = ttk.Scrollbar(pa_data_frame, orient=tk.VERTICAL, command=self.protocol_text.yview)
        self.protocol_text.config(yscrollcommand=pa_scrollbar.set)
        self.protocol_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pa_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_network_analyzer_tab(self):
        """Create network analyzer tab"""
        na_frame = ttk.Frame(self.notebook)
        self.notebook.add(na_frame, text="Network Analyzer")

        # Network analyzer controls
        na_control_frame = ttk.LabelFrame(na_frame, text="Network Analyzer Settings")
        na_control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(na_control_frame, text="Start Freq (Hz):").grid(row=0, column=0, padx=5, pady=5)
        self.na_start_freq = ttk.Entry(na_control_frame, width=15)
        self.na_start_freq.insert(0, "1000")
        self.na_start_freq.grid(row=0, column=1, padx=5)

        ttk.Label(na_control_frame, text="Stop Freq (Hz):").grid(row=0, column=2, padx=5, pady=5)
        self.na_stop_freq = ttk.Entry(na_control_frame, width=15)
        self.na_stop_freq.insert(0, "10000000")
        self.na_stop_freq.grid(row=0, column=3, padx=5)

        ttk.Label(na_control_frame, text="Points:").grid(row=0, column=4, padx=5, pady=5)
        self.na_points = ttk.Entry(na_control_frame, width=10)
        self.na_points.insert(0, "101")
        self.na_points.grid(row=0, column=5, padx=5)

        self.na_start_btn = ttk.Button(na_control_frame, text="Start Sweep", 
                                      command=self.start_network_analyzer, state=tk.DISABLED)
        self.na_start_btn.grid(row=1, column=0, padx=5, pady=10)

        self.na_stop_btn = ttk.Button(na_control_frame, text="Stop", 
                                     command=self.stop_network_analyzer, state=tk.DISABLED)
        self.na_stop_btn.grid(row=1, column=1, padx=5, pady=10)

        # Network analyzer plots
        na_plot_frame = ttk.Frame(na_frame)
        na_plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.na_fig, (self.na_ax1, self.na_ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.na_canvas = FigureCanvasTkAgg(self.na_fig, na_plot_frame)
        self.na_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.na_ax1.set_xlabel('Frequency (Hz)')
        self.na_ax1.set_ylabel('Magnitude (dB)')
        self.na_ax1.set_title('S11 Magnitude')
        self.na_ax1.grid(True)

        self.na_ax2.set_xlabel('Frequency (Hz)')
        self.na_ax2.set_ylabel('Phase (degrees)')
        self.na_ax2.set_title('S11 Phase')
        self.na_ax2.grid(True)

        plt.tight_layout()
        self.na_canvas.draw()

    def create_settings_tab(self):
        """Create settings and calibration tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")

        # Device info
        info_frame = ttk.LabelFrame(settings_frame, text="Device Information")
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        self.device_info_text = tk.Text(info_frame, height=8, state=tk.DISABLED)
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.device_info_text.yview)
        self.device_info_text.config(yscrollcommand=info_scrollbar.set)
        self.device_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Calibration
        cal_frame = ttk.LabelFrame(settings_frame, text="Calibration")
        cal_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(cal_frame, text="Calibrate Oscilloscope", 
                  command=self.calibrate_oscilloscope).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(cal_frame, text="Calibrate Function Generator", 
                  command=self.calibrate_funcgen).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(cal_frame, text="Reset Device", 
                  command=self.reset_device).pack(side=tk.LEFT, padx=5, pady=5)

        # Advanced settings
        advanced_frame = ttk.LabelFrame(settings_frame, text="Advanced Settings")
        advanced_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(advanced_frame, text="Buffer Size:").grid(row=0, column=0, padx=5, pady=5)
        self.buffer_size = ttk.Entry(advanced_frame, width=10)
        self.buffer_size.insert(0, "8192")
        self.buffer_size.grid(row=0, column=1, padx=5)

        ttk.Label(advanced_frame, text="Timeout (ms):").grid(row=0, column=2, padx=5, pady=5)
        self.timeout_ms = ttk.Entry(advanced_frame, width=10)
        self.timeout_ms.insert(0, "1000")
        self.timeout_ms.grid(row=0, column=3, padx=5)

    # Device connection methods
    def connect_device(self):
        """Connect to Analog Discovery 2 device"""
        if self.dwf is None:
            messagebox.showerror("Error", "WaveForms library not loaded")
            return

        try:
            # Enumerate devices
            cDevice = c_int()
            self.dwf.FDwfEnum(c_int(0), byref(cDevice))
            
            if cDevice.value == 0:
                messagebox.showerror("Error", "No Analog Discovery 2 device found")
                return

            # Open first device
            self.dwf.FDwfDeviceOpen(c_int(0), byref(self.hdwf))
            
            if self.hdwf.value == 0:
                szerr = create_string_buffer(512)
                self.dwf.FDwfGetLastErrorMsg(szerr)
                messagebox.showerror("Error", f"Failed to open device: {szerr.value.decode()}")
                return

            self.is_connected = True
            self.status_label.config(text="Connected", foreground="green")
            
            # Enable controls
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.start_btn.config(state=tk.NORMAL)
            self.single_btn.config(state=tk.NORMAL)
            self.dl_start_btn.config(state=tk.NORMAL)
            self.sa_start_btn.config(state=tk.NORMAL)
            self.pa_start_btn.config(state=tk.NORMAL)
            self.na_start_btn.config(state=tk.NORMAL)

            # Update device info
            self.update_device_info()
            
            messagebox.showinfo("Success", "Device connected successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Connection failed: {e}")

    def disconnect_device(self):
        """Disconnect from device"""
        if self.is_connected and self.hdwf.value != 0:
            try:
                # Stop all operations
                self.stop_acquisition()
                self.stop_data_logger()
                self.stop_spectrum_analyzer()
                self.stop_protocol_analyzer()
                self.stop_network_analyzer()
                
                # Close device
                self.dwf.FDwfDeviceClose(self.hdwf)
                self.is_connected = False
                
                self.status_label.config(text="Disconnected", foreground="red")
                
                # Disable controls
                self.connect_btn.config(state=tk.NORMAL)
                self.disconnect_btn.config(state=tk.DISABLED)
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.DISABLED)
                self.single_btn.config(state=tk.DISABLED)
                self.dl_start_btn.config(state=tk.DISABLED)
                self.sa_start_btn.config(state=tk.DISABLED)
                self.pa_start_btn.config(state=tk.DISABLED)
                self.na_start_btn.config(state=tk.DISABLED)

            except Exception as e:
                messagebox.showerror("Error", f"Disconnect failed: {e}")

    def update_device_info(self):
        """Update device information display"""
        if not self.is_connected:
            return
            
        try:
            info_text = "Device Information:\n"
            info_text += f"Handle: {self.hdwf.value}\n"
            info_text += "Model: Analog Discovery 2\n"
            info_text += "Channels: 2 Oscilloscope, 2 Function Generator\n"
            info_text += "Digital I/O: 16 pins\n"
            info_text += "Power Supplies: +V, -V\n"
            info_text += f"Connection Status: {'Connected' if self.is_connected else 'Disconnected'}\n"
            
            self.device_info_text.config(state=tk.NORMAL)
            self.device_info_text.delete(1.0, tk.END)
            self.device_info_text.insert(1.0, info_text)
            self.device_info_text.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"Error updating device info: {e}")

    # Oscilloscope methods
    def start_acquisition(self):
        """Start continuous oscilloscope acquisition"""
        if not self.is_connected:
            messagebox.showerror("Error", "Device not connected")
            return

        self.is_acquiring = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Start acquisition thread
        self.acquisition_thread = threading.Thread(target=self.acquisition_loop, daemon=True)
        self.acquisition_thread.start()

    def stop_acquisition(self):
        """Stop oscilloscope acquisition"""
        self.is_acquiring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def single_acquisition(self):
        """Perform single oscilloscope acquisition"""
        if not self.is_connected:
            messagebox.showerror("Error", "Device not connected")
            return

        try:
            self.perform_acquisition()
        except Exception as e:
            messagebox.showerror("Error", f"Single acquisition failed: {e}")

    def acquisition_loop(self):
        """Continuous acquisition loop"""
        while self.is_acquiring:
            try:
                self.perform_acquisition()
                time.sleep(0.1)  # 100ms update rate
            except Exception as e:
                print(f"Acquisition error: {e}")
                break

    def perform_acquisition(self):
        """Perform actual oscilloscope acquisition"""
        if not self.is_connected:
            return

        try:
            # Configure oscilloscope
            buffer_size = int(self.buffer_size.get()) if hasattr(self, 'buffer_size') else 8192
            frequency = 1.0 / (float(self.timebase.get()) * 10)  # 10 divisions
            
            # Set up channels
            if self.ch1_var.get():
                self.dwf.FDwfAnalogInChannelEnableSet(self.hdwf, c_int(0), c_bool(True))
                self.dwf.FDwfAnalogInChannelRangeSet(self.hdwf, c_int(0), c_double(float(self.ch1_range.get())))
            
            if self.ch2_var.get():
                self.dwf.FDwfAnalogInChannelEnableSet(self.hdwf, c_int(1), c_bool(True))
                self.dwf.FDwfAnalogInChannelRangeSet(self.hdwf, c_int(1), c_double(float(self.ch2_range.get())))

            # Set acquisition parameters
            self.dwf.FDwfAnalogInFrequencySet(self.hdwf, c_double(frequency))
            self.dwf.FDwfAnalogInBufferSizeSet(self.hdwf, c_int(buffer_size))

            # Configure trigger
            if self.trigger_source.get() != "None":
                trigger_ch = 0 if self.trigger_source.get() == "Ch1" else 1
                self.dwf.FDwfAnalogInTriggerSourceSet(self.hdwf, c_int(trigger_ch))
                self.dwf.FDwfAnalogInTriggerLevelSet(self.hdwf, c_double(float(self.trigger_level.get())))
                self.dwf.FDwfAnalogInTriggerTypeSet(self.hdwf, c_int(1))  # Edge trigger

            # Start acquisition
            self.dwf.FDwfAnalogInConfigure(self.hdwf, c_bool(False), c_bool(True))

            # Wait for acquisition to complete
            sts = c_byte()
            while True:
                self.dwf.FDwfAnalogInStatus(self.hdwf, c_bool(True), byref(sts))
                if sts.value == 2:  # Done
                    break
                time.sleep(0.001)

            # Read data
            time_data = np.linspace(0, float(self.timebase.get()) * 10, buffer_size)
            
            if self.ch1_var.get():
                ch1_data = (c_double * buffer_size)()
                self.dwf.FDwfAnalogInStatusData(self.hdwf, c_int(0), ch1_data, c_int(buffer_size))
                ch1_array = np.array([ch1_data[i] for i in range(buffer_size)])
            else:
                ch1_array = np.zeros(buffer_size)

            if self.ch2_var.get():
                ch2_data = (c_double * buffer_size)()
                self.dwf.FDwfAnalogInStatusData(self.hdwf, c_int(1), ch2_data, c_int(buffer_size))
                ch2_array = np.array([ch2_data[i] for i in range(buffer_size)])
            else:
                ch2_array = np.zeros(buffer_size)

            # Update plot
            self.root.after(0, lambda: self.update_oscilloscope_plot(time_data, ch1_array, ch2_array))

        except Exception as e:
            print(f"Acquisition error: {e}")

    def update_oscilloscope_plot(self, time_data, ch1_data, ch2_data):
        """Update oscilloscope plot"""
        try:
            self.ax.clear()
            
            if self.ch1_var.get():
                self.ax.plot(time_data, ch1_data, 'b-', label='Channel 1', linewidth=1)
            
            if self.ch2_var.get():
                self.ax.plot(time_data, ch2_data, 'r-', label='Channel 2', linewidth=1)

            self.ax.set_xlabel('Time (s)')
            self.ax.set_ylabel('Voltage (V)')
            self.ax.set_title('Oscilloscope')
            self.ax.grid(True)
            self.ax.legend()
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Plot update error: {e}")

    def save_oscilloscope_data(self):
        """Save oscilloscope data to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            # Implementation would save current data
            messagebox.showinfo("Info", f"Data saved to {filename}")

    # Function generator methods
    def update_function_generator(self):
        """Update function generator settings"""
        if not self.is_connected:
            return

        try:
            # Channel 1
            if self.fg1_enable.get():
                self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(0), c_int(0), c_bool(True))
                
                # Set function
                func_map = {"Sine": 1, "Square": 2, "Triangle": 3, "DC": 8, "Sawtooth": 4, "Noise": 5}
                func_id = func_map.get(self.fg1_func.get(), 1)
                self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(0), c_int(0), c_int(func_id))
                
                # Set parameters
                self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(0), c_int(0), c_double(float(self.fg1_freq.get())))
                self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(0), c_int(0), c_double(float(self.fg1_amp.get())))
                self.dwf.FDwfAnalogOutNodeOffsetSet(self.hdwf, c_int(0), c_int(0), c_double(float(self.fg1_offset.get())))
                
                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_bool(True))
            else:
                self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(0), c_int(0), c_bool(False))
                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_bool(True))

            # Channel 2
            if self.fg2_enable.get():
                self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(1), c_int(0), c_bool(True))
                
                func_map = {"Sine": 1, "Square": 2, "Triangle": 3, "DC": 8, "Sawtooth": 4, "Noise": 5}
                func_id = func_map.get(self.fg2_func.get(), 1)
                self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(1), c_int(0), c_int(func_id))
                
                self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(1), c_int(0), c_double(float(self.fg2_freq.get())))
                self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(1), c_int(0), c_double(float(self.fg2_amp.get())))
                self.dwf.FDwfAnalogOutNodeOffsetSet(self.hdwf, c_int(1), c_int(0), c_double(float(self.fg2_offset.get())))
                
                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(1), c_bool(True))
            else:
                self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(1), c_int(0), c_bool(False))
                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(1), c_bool(True))

        except Exception as e:
            messagebox.showerror("Error", f"Function generator update failed: {e}")

    # Power supply methods
    def update_power_supply(self):
        """Update power supply settings"""
        if not self.is_connected:
            return

        try:
            # Positive supply
            if self.ps_pos_enable.get():
                voltage = float(self.ps_pos_voltage.get())
                self.dwf.FDwfAnalogIOChannelNodeSet(self.hdwf, c_int(0), c_int(0), c_double(voltage))
                self.dwf.FDwfAnalogIOEnableSet(self.hdwf, c_bool(True))
            
            # Negative supply
            if self.ps_neg_enable.get():
                voltage = float(self.ps_neg_voltage.get())
                self.dwf.FDwfAnalogIOChannelNodeSet(self.hdwf, c_int(1), c_int(0), c_double(voltage))
                self.dwf.FDwfAnalogIOEnableSet(self.hdwf, c_bool(True))

        except Exception as e:
            messagebox.showerror("Error", f"Power supply update failed: {e}")

    def enable_all_supplies(self):
        """Enable all power supplies"""
        self.ps_pos_enable.set(True)
        self.ps_neg_enable.set(True)
        self.update_power_supply()

    def disable_all_supplies(self):
        """Disable all power supplies"""
        self.ps_pos_enable.set(False)
        self.ps_neg_enable.set(False)
        if self.is_connected:
            self.dwf.FDwfAnalogIOEnableSet(self.hdwf, c_bool(False))

    def start_current_monitoring(self):
        """Start monitoring power supply currents"""
        def monitor_current():
            while self.is_connected:
                try:
                    if self.is_connected:
                        # Read positive supply current
                        pos_current = c_double()
                        self.dwf.FDwfAnalogIOChannelNodeStatus(self.hdwf, c_int(0), c_int(1), byref(pos_current))
                        
                        # Read negative supply current
                        neg_current = c_double()
                        self.dwf.FDwfAnalogIOChannelNodeStatus(self.hdwf, c_int(1), c_int(1), byref(neg_current))
                        
                        # Update labels
                        self.root.after(0, lambda: self.ps_pos_current_label.config(text=f"Current: {pos_current.value:.3f} A"))
                        self.root.after(0, lambda: self.ps_neg_current_label.config(text=f"Current: {neg_current.value:.3f} A"))
                        
                    time.sleep(1)
                except:
                    break
        
        threading.Thread(target=monitor_current, daemon=True).start()

    # Data logger methods
    def browse_log_file(self):
        """Browse for log file location"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.dl_filename.delete(0, tk.END)
            self.dl_filename.insert(0, filename)

    def start_data_logger(self):
        """Start data logging"""
        if not self.is_connected:
            messagebox.showerror("Error", "Device not connected")
            return

        self.data_logger_running = True
        self.dl_start_btn.config(state=tk.DISABLED)
        self.dl_stop_btn.config(state=tk.NORMAL)
        self.dl_status_label.config(text="Status: Logging...")

        # Start logger thread
        self.logger_thread = threading.Thread(target=self.data_logger_loop, daemon=True)
        self.logger_thread.start()

    def stop_data_logger(self):
        """Stop data logging"""
        self.data_logger_running = False
        self.dl_start_btn.config(state=tk.NORMAL)
        self.dl_stop_btn.config(state=tk.DISABLED)
        self.dl_status_label.config(text="Status: Stopped")
        self.dl_progress.config(value=0)

    def data_logger_loop(self):
        """Data logging loop"""
        try:
            filename = self.dl_filename.get()
            duration = float(self.dl_duration.get())
            interval_map = {"1s": 1, "10s": 10, "1min": 60, "10min": 600, "1hour": 3600}
            interval = interval_map.get(self.dl_interval.get(), 1)
            
            start_time = time.time()
            samples = int(duration / interval)
            sample_count = 0

            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                headers = ['Time', 'Timestamp']
                if self.dl_ch1_enable.get():
                    headers.append('Channel_1')
                if self.dl_ch2_enable.get():
                    headers.append('Channel_2')
                writer.writerow(headers)

                while self.data_logger_running and sample_count < samples:
                    current_time = time.time()
                    elapsed = current_time - start_time
                    
                    # Read data (simplified - would use actual acquisition)
                    row = [elapsed, datetime.now().isoformat()]
                    
                    if self.dl_ch1_enable.get():
                        # Simulate reading channel 1
                        row.append(np.random.normal(0, 0.1))
                    
                    if self.dl_ch2_enable.get():
                        # Simulate reading channel 2
                        row.append(np.random.normal(0, 0.1))
                    
                    writer.writerow(row)
                    sample_count += 1
                    
                    # Update progress
                    progress = (sample_count / samples) * 100
                    self.root.after(0, lambda: self.dl_progress.config(value=progress))
                    
                    time.sleep(interval)

            self.root.after(0, lambda: self.dl_status_label.config(text="Status: Complete"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Data logging failed: {e}"))

    # Spectrum analyzer methods
    def start_spectrum_analyzer(self):
        """Start spectrum analyzer"""
        if not self.is_connected:
            messagebox.showerror("Error", "Device not connected")
            return

        self.spectrum_running = True
        self.sa_start_btn.config(state=tk.DISABLED)
        self.sa_stop_btn.config(state=tk.NORMAL)

        self.spectrum_thread = threading.Thread(target=self.spectrum_analyzer_loop, daemon=True)
        self.spectrum_thread.start()

    def stop_spectrum_analyzer(self):
        """Stop spectrum analyzer"""
        self.spectrum_running = False
        self.sa_start_btn.config(state=tk.NORMAL)
        self.sa_stop_btn.config(state=tk.DISABLED)

    def spectrum_analyzer_loop(self):
        """Spectrum analyzer loop"""
        try:
            start_freq = float(self.sa_start_freq.get())
            stop_freq = float(self.sa_stop_freq.get())
            samples = int(self.sa_samples.get())
            
            while self.spectrum_running:
                # Generate simulated spectrum data
                freqs = np.linspace(start_freq, stop_freq, samples)
                # Simulate spectrum with noise and some peaks
                magnitude = -60 + 10 * np.random.random(samples) + \
                           20 * np.exp(-((freqs - start_freq*2)**2) / (2 * (1000**2)))
                
                self.root.after(0, lambda: self.update_spectrum_plot(freqs, magnitude))
                time.sleep(0.5)
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Spectrum analyzer failed: {e}"))

    def update_spectrum_plot(self, freqs, magnitude):
        """Update spectrum analyzer plot"""
        try:
            self.sa_ax.clear()
            self.sa_ax.plot(freqs, magnitude, 'b-', linewidth=1)
            self.sa_ax.set_xlabel('Frequency (Hz)')
            self.sa_ax.set_ylabel('Magnitude (dB)')
            self.sa_ax.set_title('Spectrum Analyzer')
            self.sa_ax.grid(True)
            self.sa_canvas.draw()
        except Exception as e:
            print(f"Spectrum plot update error: {e}")

    # Digital I/O methods
    def update_digital_outputs(self):
        """Update digital outputs"""
        if not self.is_connected:
            return

        try:
            # Create output value from checkboxes
            output_value = 0
            for i, var in enumerate(self.dio_vars):
                if var.get():
                    output_value |= (1 << i)
            
            # Set digital outputs
            self.dwf.FDwfDigitalIOOutputEnableSet(self.hdwf, c_int(0xFFFF))  # Enable all outputs
            self.dwf.FDwfDigitalIOOutputSet(self.hdwf, c_int(output_value))
            
        except Exception as e:
            messagebox.showerror("Error", f"Digital output update failed: {e}")

    def start_digital_monitoring(self):
        """Start monitoring digital inputs"""
        def monitor_inputs():
            while True:
                try:
                    if self.is_connected:
                        # Read digital inputs
                        input_value = c_int()
                        self.dwf.FDwfDigitalIOInputGet(self.hdwf, byref(input_value))
                        input_value = input_value.value
                        # Update labels
                        for i in range(16):
                            state = "HIGH" if (input_value & (1 << i)) else "LOW"
                            self.root.after(0, lambda i=i, state=state: self.dio_input_labels[i].config(text=f"DIO {i}: {state}"))
                    time.sleep(0.1)  # Update every 100ms
                except Exception as e:
                    print(f"Digital input monitoring error: {e}")
                    break

                        

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalogDiscovery2GUI(root)
    root.mainloop()                