import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import threading
import time
from ctypes import *
import sys
import os

class AnalogDiscovery2GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analog Discovery 2 Control")
        self.root.geometry("1000x700")
        
        # Device handle
        self.hdwf = c_int()
        self.is_connected = False
        self.is_acquiring = False
        
        # Load WaveForms library
        self.dwf = None
        self.load_dwf_library()
        
        # Create GUI
        self.create_widgets()
        
        # Initialize device
        self.connect_device()
        
    def load_dwf_library(self):
        """Load the WaveForms library based on system architecture"""
        try:
            if sys.platform.startswith("win"):
                # For 32-bit Python on Windows
                if "32 bit" in sys.version or sys.maxsize <= 2**32:
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
            
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
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
        
        self.disconnect_btn = ttk.Button(control_frame, text="Disconnect", command=self.disconnect_device, state=tk.DISABLED)
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
        self.ch1_range = ttk.Combobox(osc_control_frame, values=["0.5", "1", "2", "5", "10", "25"], state="readonly", width=8)
        self.ch1_range.set("5")
        self.ch1_range.grid(row=0, column=3, padx=5)
        
        ttk.Label(osc_control_frame, text="Channel 2:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.ch2_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(osc_control_frame, text="Enable", variable=self.ch2_var).grid(row=1, column=1, padx=5)
        
        ttk.Label(osc_control_frame, text="Range (V):").grid(row=1, column=2, padx=5)
        self.ch2_range = ttk.Combobox(osc_control_frame, values=["0.5", "1", "2", "5", "10", "25"], state="readonly", width=8)
        self.ch2_range.set("5")
        self.ch2_range.grid(row=1, column=3, padx=5)
        
        # Timebase control
        ttk.Label(osc_control_frame, text="Timebase (s/div):").grid(row=0, column=4, padx=5)
        self.timebase = ttk.Combobox(osc_control_frame, values=["1e-6", "2e-6", "5e-6", "1e-5", "2e-5", "5e-5", "1e-4", "2e-4", "5e-4", "1e-3", "2e-3", "5e-3"], state="readonly", width=10)
        self.timebase.set("1e-4")
        self.timebase.grid(row=0, column=5, padx=5)
        
        # Acquisition controls
        self.start_btn = ttk.Button(osc_control_frame, text="Start", command=self.start_acquisition, state=tk.DISABLED)
        self.start_btn.grid(row=1, column=4, padx=5, pady=5)
        
        self.stop_btn = ttk.Button(osc_control_frame, text="Stop", command=self.stop_acquisition, state=tk.DISABLED)
        self.stop_btn.grid(row=1, column=5, padx=5, pady=5)
        
        self.single_btn = ttk.Button(osc_control_frame, text="Single", command=self.single_acquisition, state=tk.DISABLED)
        self.single_btn.grid(row=1, column=6, padx=5, pady=5)
        
        # Plot frame
        plot_frame = ttk.Frame(osc_frame)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 4))
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
        ttk.Checkbutton(funcgen_control_frame, text="Enable", variable=self.fg1_enable, command=self.update_function_generator).grid(row=0, column=1, padx=5)
        
        ttk.Label(funcgen_control_frame, text="Waveform:").grid(row=0, column=2, padx=5)
        self.fg1_func = ttk.Combobox(funcgen_control_frame, values=["Sine", "Square", "Triangle", "DC"], state="readonly", width=10)
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
        
        # Channel 2 controls
        ttk.Label(funcgen_control_frame, text="Ch2:").grid(row=1, column=0, padx=5)
        self.fg2_enable = tk.BooleanVar()
        ttk.Checkbutton(funcgen_control_frame, text="Enable", variable=self.fg2_enable, command=self.update_function_generator).grid(row=1, column=1, padx=5)
        
        ttk.Label(funcgen_control_frame, text="Waveform:").grid(row=1, column=2, padx=5)
        self.fg2_func = ttk.Combobox(funcgen_control_frame, values=["Sine", "Square", "Triangle", "DC"], state="readonly", width=10)
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
        
    def connect_device(self):
        """Connect to Analog Discovery 2"""
        if not self.dwf:
            messagebox.showerror("Error", "WaveForms library not loaded")
            return
            
        try:
            # Enumerate devices
            cDevice = c_int()
            self.dwf.FDwfEnum(c_int(0), byref(cDevice))
            
            if cDevice.value == 0:
                messagebox.showerror("Error", "No Analog Discovery 2 device found")
                return
                
            # Open device
            self.dwf.FDwfDeviceOpen(c_int(0), byref(self.hdwf))
            
            if self.hdwf.value == 0:
                messagebox.showerror("Error", "Failed to open Analog Discovery 2")
                return
                
            self.is_connected = True
            self.status_label.config(text="Connected", foreground="green")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.start_btn.config(state=tk.NORMAL)
            self.single_btn.config(state=tk.NORMAL)
            
            # Configure default settings
            self.configure_oscilloscope()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {e}")
            
    def disconnect_device(self):
        """Disconnect from Analog Discovery 2"""
        if self.is_connected and self.dwf:
            self.stop_acquisition()
            self.dwf.FDwfDeviceClose(self.hdwf)
            
        self.is_connected = False
        self.status_label.config(text="Disconnected", foreground="red")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.single_btn.config(state=tk.DISABLED)
        
    def configure_oscilloscope(self):
        """Configure oscilloscope settings"""
        if not self.is_connected:
            return
            
        try:
            # Set up analog input channels
            for ch in range(2):
                # Enable channel
                self.dwf.FDwfAnalogInChannelEnableSet(self.hdwf, c_int(ch), c_bool(True))
                
                # Set range
                range_val = float(self.ch1_range.get() if ch == 0 else self.ch2_range.get())
                self.dwf.FDwfAnalogInChannelRangeSet(self.hdwf, c_int(ch), c_double(range_val))
                
            # Set acquisition parameters
            sample_rate = 20e6  # 20 MHz
            buffer_size = 8192
            
            self.dwf.FDwfAnalogInFrequencySet(self.hdwf, c_double(sample_rate))
            self.dwf.FDwfAnalogInBufferSizeSet(self.hdwf, c_int(buffer_size))
            
        except Exception as e:
            print(f"Error configuring oscilloscope: {e}")
            
    def start_acquisition(self):
        """Start continuous acquisition"""
        if not self.is_connected:
            return
            
        self.is_acquiring = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Start acquisition in separate thread
        self.acquisition_thread = threading.Thread(target=self.acquisition_loop)
        self.acquisition_thread.daemon = True
        self.acquisition_thread.start()
        
    def stop_acquisition(self):
        """Stop acquisition"""
        self.is_acquiring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
    def single_acquisition(self):
        """Single acquisition"""
        if not self.is_connected:
            return
            
        try:
            # Configure and start single acquisition
            self.configure_oscilloscope()
            self.dwf.FDwfAnalogInConfigure(self.hdwf, c_bool(False), c_bool(True))
            
            # Wait for acquisition to complete
            sts = c_byte()
            while True:
                self.dwf.FDwfAnalogInStatus(self.hdwf, c_int(1), byref(sts))
                if sts.value == 2:  # DwfStateDone
                    break
                time.sleep(0.001)
                
            # Read data
            self.read_and_plot_data()
            
        except Exception as e:
            print(f"Error in single acquisition: {e}")
            
    def acquisition_loop(self):
        """Continuous acquisition loop"""
        try:
            # Start continuous acquisition
            self.dwf.FDwfAnalogInConfigure(self.hdwf, c_bool(False), c_bool(True))
            
            while self.is_acquiring:
                sts = c_byte()
                self.dwf.FDwfAnalogInStatus(self.hdwf, c_int(1), byref(sts))
                
                if sts.value == 2:  # DwfStateDone
                    self.read_and_plot_data()
                    # Restart acquisition
                    self.dwf.FDwfAnalogInConfigure(self.hdwf, c_bool(False), c_bool(True))
                    
                time.sleep(0.05)  # 20 FPS update rate
                
        except Exception as e:
            print(f"Error in acquisition loop: {e}")
            
    def read_and_plot_data(self):
        """Read data from device and update plot"""
        try:
            buffer_size = 8192
            ch1_data = (c_double * buffer_size)()
            ch2_data = (c_double * buffer_size)()
            
            # Read channel data
            self.dwf.FDwfAnalogInStatusData(self.hdwf, c_int(0), ch1_data, c_int(buffer_size))
            self.dwf.FDwfAnalogInStatusData(self.hdwf, c_int(1), ch2_data, c_int(buffer_size))
            
            # Convert to numpy arrays
            ch1_array = np.array([ch1_data[i] for i in range(buffer_size)])
            ch2_array = np.array([ch2_data[i] for i in range(buffer_size)])
            
            # Create time axis
            sample_rate = 20e6
            time_axis = np.arange(buffer_size) / sample_rate
            
            # Update plot
            self.ax.clear()
            
            if self.ch1_var.get():
                self.ax.plot(time_axis, ch1_array, 'b-', label='Channel 1', linewidth=1)
                
            if self.ch2_var.get():
                self.ax.plot(time_axis, ch2_array, 'r-', label='Channel 2', linewidth=1)
                
            self.ax.set_xlabel('Time (s)')
            self.ax.set_ylabel('Voltage (V)')
            self.ax.set_title('Oscilloscope')
            self.ax.grid(True)
            self.ax.legend()
            
            # Set time axis based on timebase setting
            timebase = float(self.timebase.get())
            self.ax.set_xlim(0, timebase * 10)
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error reading data: {e}")
            
    def update_function_generator(self):
        """Update function generator settings"""
        if not self.is_connected:
            return
            
        try:
            # Function type mapping
            func_map = {"Sine": 1, "Square": 2, "Triangle": 3, "DC": 8}
            
            # Configure Channel 1
            if self.fg1_enable.get():
                func_type = func_map.get(self.fg1_func.get(), 1)
                frequency = float(self.fg1_freq.get())
                amplitude = float(self.fg1_amp.get())
                
                self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(0), c_int(0), c_bool(True))
                self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(0), c_int(0), c_int(func_type))
                self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(0), c_int(0), c_double(frequency))
                self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(0), c_int(0), c_double(amplitude))
                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_bool(True))
            else:
                self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(0), c_int(0), c_bool(False))
                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_bool(True))
                
            # Configure Channel 2
            if self.fg2_enable.get():
                func_type = func_map.get(self.fg2_func.get(), 1)
                frequency = float(self.fg2_freq.get())
                amplitude = float(self.fg2_amp.get())
                
                self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(1), c_int(0), c_bool(True))
                self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(1), c_int(0), c_int(func_type))
                self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(1), c_int(0), c_double(frequency))
                self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(1), c_int(0), c_double(amplitude))
                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(1), c_bool(True))
            else:
                self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(1), c_int(0), c_bool(False))
                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(1), c_bool(True))
                
        except Exception as e:
            print(f"Error updating function generator: {e}")
            
    def __del__(self):
        """Cleanup when object is destroyed"""
        if self.is_connected:
            self.disconnect_device()

def main():
    root = tk.Tk()
    app = AnalogDiscovery2GUI(root)
    
    # Handle window close
    def on_closing():
        app.disconnect_device()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()