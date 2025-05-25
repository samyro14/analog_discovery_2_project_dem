import ctypes
from ctypes import c_int, c_char_p, c_double, c_bool
from dwfconstants import DwfState, DwfTriggerSource
import time

dwf = ctypes.cdll.LoadLibrary("dwf.dll")

# Buffere pentru comunicare
hdwf = c_int()
version = ctypes.create_string_buffer(16)

# Află versiunea WaveForms SDK
dwf.FDwfGetVersion(version)
print("WaveForms SDK version:", version.value.decode())

# Încearcă să deschidă primul device (Analog Discovery 2)
print("Deschidere AD2...")
dwf.FDwfDeviceOpen(0, ctypes.byref(hdwf))

if hdwf.value == 0:
    err = ctypes.create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(err)
    print("Eroare:", err.value.decode())
else:
    print("Device conectat cu handle =", hdwf.value)

    # Opțional: citim temperatura internă
    temp = c_double()
    dwf.FDwfAnalogInTemperatureStatus(hdwf, None, ctypes.byref(temp))
    print(f"Temperatură internă: {temp.value:.2f} °C")

    # Închidem device-ul
    dwf.FDwfDeviceClose(hdwf)