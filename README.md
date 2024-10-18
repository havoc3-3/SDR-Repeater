# SDR-Repeater

An SDR-based repeater capable of cross-band signal repeating, supporting analog, digital, and encrypted modes.
Dependencies

    GNU Radio (built from source)
    OsmoSDR (built from source)
    Python
    SDR device drivers (RTL-SDR, BladeRF, etc.) (built from source)

# Function

This script functions as a real-time RF repeater. It monitors two frequencies using two different SDR devices and dynamically forwards the strongest detected signal to the transmitter on a corresponding frequency.

The transmitter's frequency is automatically adjusted based on the detected signal. If RX1 detects a stronger signal, the transmitter will switch to tx1_freq. If RX2 has a stronger signal, it will switch to tx2_freq.

The system does not demodulate the incoming signal or remodulate the outgoing signal. Instead, it forwards the raw RF signal as received, allowing it to handle digital and encrypted communications (as long as the receiving radios are configured with the correct encryption keys).

This setup supports cross-band transmission across any frequency range compatible with your SDR hardware, such as UHF to VHF, VHF to UHF, UHF to HF, etc. All FCC regulations apply.

# Example 
    python repeater.py --rx1-args "rtl=0" --rx1-freq [150.000e6] --rx2-args "bladerf=0" --rx2-freq [450.000e6] --tx-args "bladerf=0" --tx1-freq [450.000e6] --tx2-freq [150.000e6]
