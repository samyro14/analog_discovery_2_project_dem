import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from ctypes import *
import sys
import math


class AnalogDiscovery2GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analog Discovery 2 Control")
        self.root.geometry("1200x800")

        # Device handle
        self.hdwf = c_int()
        self.is_connected = False
        self.is_acquiring = False

        # Plot data storage
        self.ch1_data = []
        self.ch2_data = []
        self.time_data = []
        self.plot_width = 800
        self.plot_height = 300

        # Load WaveForms library
        self.dwf = None

        # Create GUI
        self.create_widgets()

        # Try to load library after GUI is created
        self.load_dwf_library()

    def load_dwf_library(self):
        """Load the WaveForms library based on system architecture"""
        try:
            if sys.platform.startswith("win"):
                # For Windows - try both 32-bit and 64-bit locations
                try:
                    self.dwf = cdll.LoadLibrary("dwf.dll")
                except:
                    # Try alternative paths
                    import os
                    possible_paths = [
                        r"C:\Program Files (x86)\Digilent\WaveFormsSDK\lib\dwf.dll",
                        r"C:\Program Files\Digilent\WaveFormsSDK\lib\dwf.dll",
                        r"dwf.dll"
                    ]
                    for path in possible_paths:
                        try:
                            if os.path.exists(path):
                                self.dwf = cdll.LoadLibrary(path)
                                break
                        except:
                            continue
                    else:
                        raise Exception("dwf.dll not found in standard locations")

            elif sys.platform.startswith("darwin"):
                self.dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
            else:
                self.dwf = cdll.LoadLibrary("libdwf.so")

            self.status_label.config(text="WaveForms library loaded successfully", foreground="green")

        except Exception as e:
            self.status_label.config(text=f"WaveForms library not found: {str(e)}", foreground="orange")

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

        self.disconnect_btn = ttk.Button(control_frame, text="Disconnect", command=self.disconnect_device,
                                         state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=3, padx=5, pady=5)

        # Test mode button
        self.test_btn = ttk.Button(control_frame, text="Test Mode", command=self.enable_test_mode)
        self.test_btn.grid(row=0, column=4, padx=5, pady=5)

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

        # Acquisition controls
        self.start_btn = ttk.Button(osc_control_frame, text="Start", command=self.start_acquisition, state=tk.DISABLED)
        self.start_btn.grid(row=1, column=4, padx=5, pady=5)

        self.stop_btn = ttk.Button(osc_control_frame, text="Stop", command=self.stop_acquisition, state=tk.DISABLED)
        self.stop_btn.grid(row=1, column=5, padx=5, pady=5)

        self.single_btn = ttk.Button(osc_control_frame, text="Single", command=self.single_acquisition,
                                     state=tk.DISABLED)
        self.single_btn.grid(row=1, column=6, padx=5, pady=5)

        # Plot frame with Canvas
        plot_frame = ttk.LabelFrame(osc_frame, text="Waveform Display")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create canvas for plotting
        self.canvas = tk.Canvas(plot_frame, bg='black', height=300)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bind canvas resize and configure
        self.canvas.bind('<Configure>', self.on_canvas_configure)

        # Initialize plot
        self.root.after(100, self.init_plot)

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
        self.fg1_func = ttk.Combobox(funcgen_control_frame, values=["Sine", "Square", "Triangle", "DC"],
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

        # Channel 2 controls
        ttk.Label(funcgen_control_frame, text="Ch2:").grid(row=1, column=0, padx=5)
        self.fg2_enable = tk.BooleanVar()
        ttk.Checkbutton(funcgen_control_frame, text="Enable", variable=self.fg2_enable,
                        command=self.update_function_generator).grid(row=1, column=1, padx=5)

        ttk.Label(funcgen_control_frame, text="Waveform:").grid(row=1, column=2, padx=5)
        self.fg2_func = ttk.Combobox(funcgen_control_frame, values=["Sine", "Square", "Triangle", "DC"],
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

        # Data display frame
        data_frame = ttk.LabelFrame(main_frame, text="Data Information")
        data_frame.pack(fill=tk.X, pady=(5, 0))

        self.data_label = ttk.Label(data_frame, text="No data acquired")
        self.data_label.pack(padx=5, pady=5)

    def init_plot(self):
        """Initialize the plot display"""
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width > 1 and height > 1:  # Make sure canvas is properly sized
            self.plot_width = width
            self.plot_height = height
            self.draw_grid()
            self.canvas.create_text(width // 2, height // 2,
                                    text="Connect device and start acquisition\n(or use Test Mode)",
                                    fill="white", font=("Arial", 12), justify=tk.CENTER)
        else:
            # Try again later if canvas isn't ready
            self.root.after(100, self.init_plot)

    def on_canvas_configure(self, event):
        """Handle canvas resize event"""
        self.plot_width = event.width
        self.plot_height = event.height
        if hasattr(self, 'ch1_data') and self.ch1_data:
            self.update_plot()
        else:
            self.draw_grid()

    def draw_grid(self):
        """Draw grid on canvas"""
        self.canvas.delete("grid")

        # Draw grid lines
        grid_color = "#333333"

        # Vertical lines
        for i in range(0, self.plot_width, self.plot_width // 10):
            self.canvas.create_line(i, 0, i, self.plot_height, fill=grid_color, tags="grid")

        # Horizontal lines
        for i in range(0, self.plot_height, self.plot_height // 8):
            self.canvas.create_line(0, i, self.plot_width, i, fill=grid_color, tags="grid")

        # Center lines (brighter)
        center_x = self.plot_width // 2
        center_y = self.plot_height // 2
        self.canvas.create_line(center_x, 0, center_x, self.plot_height, fill="#666666", tags="grid")
        self.canvas.create_line(0, center_y, self.plot_width, center_y, fill="#666666", tags="grid")

    def enable_test_mode(self):
        """Enable test mode for demonstration without hardware"""
        self.is_connected = True
        self.status_label.config(text="Test Mode Active", foreground="blue")
        self.connect_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.NORMAL)
        self.start_btn.config(state=tk.NORMAL)
        self.single_btn.config(state=tk.NORMAL)
        self.test_btn.config(state=tk.DISABLED)

        # Generate test data
        self.generate_test_data()
        self.update_plot()

    def generate_test_data(self):
        """Generate test waveform data"""
        import random

        # Generate time axis
        sample_rate = 20000  # 20 kHz for demo
        duration = 0.01  # 10ms
        samples = int(sample_rate * duration)

        self.time_data = [i / sample_rate for i in range(samples)]

        # Generate Channel 1 - Sine wave with noise
        freq1 = float(self.fg1_freq.get()) if self.fg1_freq.get() else 1000
        amp1 = float(self.fg1_amp.get()) if self.fg1_amp.get() else 1
        self.ch1_data = []
        for t in self.time_data:
            signal = amp1 * math.sin(2 * math.pi * freq1 * t)
            noise = random.uniform(-0.1, 0.1)  # Add some noise
            self.ch1_data.append(signal + noise)

        # Generate Channel 2 - Square wave
        freq2 = float(self.fg2_freq.get()) if self.fg2_freq.get() else 2000
        amp2 = float(self.fg2_amp.get()) if self.fg2_amp.get() else 1
        self.ch2_data = []
        for t in self.time_data:
            if math.sin(2 * math.pi * freq2 * t) > 0:
                signal = amp2
            else:
                signal = -amp2
            noise = random.uniform(-0.05, 0.05)
            self.ch2_data.append(signal + noise)

        # Update data info
        self.data_label.config(text=f"Test data: {len(self.ch1_data)} samples, Rate: {sample_rate} Hz")

    def connect_device(self):
        """Connect to Analog Discovery 2"""
        if not self.dwf:
            messagebox.showerror("Error",
                                 "WaveForms library not loaded. Please install WaveForms software or use Test Mode.")
            return

        try:
            # Enumerate devices
            cDevice = c_int()
            self.dwf.FDwfEnum(c_int(0), byref(cDevice))

            if cDevice.value == 0:
                messagebox.showerror("Error", "No Analog Discovery 2 device found. Try Test Mode for demonstration.")
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
            self.test_btn.config(state=tk.DISABLED)

            # Configure default settings
            self.configure_oscilloscope()

            # Clear canvas and show ready message
            self.canvas.delete("all")
            self.draw_grid()
            self.canvas.create_text(self.plot_width // 2, self.plot_height // 2,
                                    text="Device connected - Ready for acquisition",
                                    fill="green", font=("Arial", 12))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {e}")

    def disconnect_device(self):
        """Disconnect from Analog Discovery 2"""
        if self.is_connected and self.dwf and hasattr(self, 'hdwf'):
            self.stop_acquisition()
            try:
                self.dwf.FDwfDeviceClose(self.hdwf)
            except:
                pass

        self.is_connected = False
        self.status_label.config(text="Disconnected", foreground="red")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.single_btn.config(state=tk.DISABLED)
        self.test_btn.config(state=tk.NORMAL)

        # Clear data
        self.ch1_data = []
        self.ch2_data = []
        self.time_data = []

        # Clear canvas
        self.canvas.delete("all")
        self.draw_grid()
        self.canvas.create_text(self.plot_width // 2, self.plot_height // 2,
                                text="Device disconnected", fill="red", font=("Arial", 12))
        self.data_label.config(text="No data acquired")

    def configure_oscilloscope(self):
        """Configure oscilloscope settings"""
        if not self.is_connected or not self.dwf:
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
            timebase_val = float(self.timebase.get())
            # Adjust sample rate based on timebase (s/div, 10 divs total)
            sample_rate = 10.0 / (timebase_val * buffer_size)
            if sample_rate > 20e6:
                sample_rate = 20e6  # Cap at 20 MHz

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
        if hasattr(self, 'start_btn'):
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    def single_acquisition(self):
        """Single acquisition"""
        if not self.is_connected:
            return

        if self.status_label.cget("text") == "Test Mode Active":
            # Generate new test data
            self.generate_test_data()
            self.update_plot()
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
        if self.status_label.cget("text") == "Test Mode Active":
            # Test mode continuous acquisition
            while self.is_acquiring:
                self.generate_test_data()
                self.root.after(0, self.update_plot)  # Thread-safe GUI update
                time.sleep(0.1)  # 10 FPS update rate
            return

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

            # Convert to lists
            self.ch1_data = [ch1_data[i] for i in range(buffer_size)]
            self.ch2_data = [ch2_data[i] for i in range(buffer_size)]

            # Create time axis
            sample_rate = 20e6
            timebase_val = float(self.timebase.get())
            samples = int(sample_rate * timebase_val * 10)  # 10 divisions
            if samples > buffer_size:
                samples = buffer_size
            self.time_data = [i / sample_rate for i in range(samples)]
            self.ch1_data = self.ch1_data[:samples]
            self.ch2_data = self.ch2_data[:samples]

            # Update data info
            self.data_label.config(text=f"Data: {len(self.ch1_data)} samples, Rate: {sample_rate / 1e6:.2f} MHz")

            # Update plot
            self.update_plot()

        except Exception as e:
            print(f"Error reading data: {e}")

    def update_plot(self):
        """Update the waveform plot"""
        if not self.ch1_data and not self.ch2_data:
            return

        # Clear previous waveforms but keep grid
        self.canvas.delete("waveform")
        self.draw_grid()

        if not self.time_data:
            return

        # Calculate scaling
        margin = 20
        plot_area_width = self.plot_width - 2 * margin
        plot_area_height = self.plot_height - 2 * margin

        if len(self.time_data) < 2:
            return

        # Time scaling
        time_min, time_max = min(self.time_data), max(self.time_data)
        time_range = time_max - time_min
        if time_range == 0:
            return

        # Voltage scaling - find max range from enabled channels
        voltage_max = 0
        if self.ch1_var.get() and self.ch1_data:
            voltage_max = max(voltage_max, max(abs(min(self.ch1_data)), abs(max(self.ch1_data))))
        if self.ch2_var.get() and self.ch2_data:
            voltage_max = max(voltage_max, max(abs(min(self.ch2_data)), abs(max(self.ch2_data))))

        if voltage_max == 0:
            voltage_max = float(self.ch1_range.get())  # Use range setting as fallback

        voltage_scale = plot_area_height / (2 * voltage_max)
        center_y = self.plot_height // 2

        # Plot Channel 1
        if self.ch1_var.get() and self.ch1_data:
            points = []
            for i, (t, v) in enumerate(zip(self.time_data, self.ch1_data)):
                x = margin + (t - time_min) / time_range * plot_area_width
                y = center_y - v * voltage_scale
                points.extend([x, y])

            if len(points) >= 4:  # Need at least 2 points
                self.canvas.create_line(points, fill="cyan", width=1, tags="waveform")

        # Plot Channel 2
        if self.ch2_var.get() and self.ch2_data:
            points = []
            for i, (t, v) in enumerate(zip(self.time_data, self.ch2_data)):
                x = margin + (t - time_min) / time_range * plot_area_width
                y = center_y - v * voltage_scale
                points.extend([x, y])

            if len(points) >= 4:  # Need at least 2 points
                self.canvas.create_line(points, fill="yellow", width=1, tags="waveform")

        # Add scale labels
        self.canvas.create_text(10, 20, text=f"+{voltage_max:.2f}V", fill="white", anchor="nw", tags="waveform")
        self.canvas.create_text(10, self.plot_height - 20, text=f"-{voltage_max:.2f}V", fill="white", anchor="sw",
                                tags="waveform")
        # Add time axis labels (10 divisions)
        time_per_div = time_range / 10
        for i in range(11):
            x = margin + i * (plot_area_width / 10)
            t = time_min + i * time_per_div
            self.canvas.create_text(x, self.plot_height - 10, text=f"{t * 1e6:.1f}µs", fill="white", anchor="s",
                                    tags="waveform")

        # Add channel labels
        if self.ch1_var.get():
            self.canvas.create_text(10, 40, text="Ch1", fill="cyan", anchor="nw", tags="waveform")
        if self.ch2_var.get():
            self.canvas.create_text(40, 40, text="Ch2", fill="yellow", anchor="nw", tags="waveform")

    def update_function_generator(self):
        """Configure function generator settings"""
        if not self.is_connected or not self.dwf:
            if self.status_label.cget("text") == "Test Mode Active":
                self.generate_test_data()
                self.update_plot()
            return

        try:
            # Waveform types mapping
            waveform_map = {
                "Sine": 0,  # DwfAnalogOutFunctionSine
                "Square": 1,  # DwfAnalogOutFunctionSquare
                "Triangle": 2,  # DwfAnalogOutFunctionTriangle
                "DC": 6  # DwfAnalogOutFunctionDC
            }

            # Configure Channel 1
            if self.fg1_enable.get():
                channel = 0
                self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(channel), c_int(0), c_bool(True))
                waveform = waveform_map[self.fg1_func.get()]
                self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(channel), c_int(0), c_byte(waveform))

                freq = float(self.fg1_freq.get()) if self.fg1_freq.get() else 1000
                self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(channel), c_int(0), c_double(freq))

                amp = float(self.fg1_amp.get()) if self.fg1_amp.get() else 1
                self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(channel), c_int(0), c_double(amp))

                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(channel), c_bool(True))
            else:
                self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(0), c_int(0), c_bool(False))
                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_bool(False))

            # Configure Channel 2
            if self.fg2_enable.get():
                channel = 1
                self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(channel), c_int(0), c_bool(True))
                waveform = waveform_map[self.fg2_func.get()]
                self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(channel), c_int(0), c_byte(waveform))

                freq = float(self.fg2_freq.get()) if self.fg2_freq.get() else 2000
                self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(channel), c_int(0), c_double(freq))

                amp = float(self.fg2_amp.get()) if self.fg2_amp.get() else 1
                self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(channel), c_int(0), c_double(amp))

                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(channel), c_bool(True))
            else:
                self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(1), c_int(0), c_bool(False))
                self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(1), c_bool(False))

        except Exception as e:
            print(f"Error configuring function generator: {e}")
            messagebox.showerror("Error", f"Failed to configure function generator: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AnalogDiscovery2GUI(root)
    root.mainloop()