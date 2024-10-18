import time
from gnuradio import gr, blocks
import osmosdr
from optparse import OptionParser

# ANSI escape codes for red and bold text
BOLD_RED = '\033[1;31m'
RESET = '\033[0m'

print(f"{BOLD_RED}DO NOT TRANSMIT ON FREQUENCIES YOU DO NOT HAVE A LICENSE FOR. Ensure you follow all FCC rules regarding transmit power and digital modes on specific frequencies{RESET}")

class dynamic_relay(gr.top_block):
    def __init__(self, rx1_freq, tx1_freq, rx2_freq, tx2_freq, rx1_args, rx2_args, tx_args, sample_rate):
        gr.top_block.__init__(self)

        # Store frequency values
        self.tx1_freq = tx1_freq
        self.tx2_freq = tx2_freq

        # Receiver setup for RX1 (RTL-SDR, BladeRF, USRP, HackRF, etc...)
        self.rx1_source = osmosdr.source(rx1_args)
        self.rx1_source.set_sample_rate(sample_rate)
        self.rx1_source.set_center_freq(rx1_freq)
        self.rx1_source.set_gain(40, 0)

        # Receiver setup for RX2 (RTL-SDR, BladeRF, USRP, HackRF, etc...)
        self.rx2_source = osmosdr.source(rx2_args)
        self.rx2_source.set_sample_rate(sample_rate)
        self.rx2_source.set_center_freq(rx2_freq)
        self.rx2_source.set_gain(30, 0)

        # Transmitter setup (BladeRF, HackRF, USRP, LimeSDR, etc...)
        # Currently set up to only use one transmitter
        self.tx_sink = osmosdr.sink(tx_args)
        self.tx_sink.set_sample_rate(sample_rate)
        self.tx_sink.set_gain(20, 0)  # Set gain

        # Probe signal power for RX1 and RX2
        self.rx1_probe = blocks.probe_signal_f()
        self.rx2_probe = blocks.probe_signal_f()

        # Add probes to monitor signal power
        self.connect(self.rx1_source, blocks.complex_to_mag_squared(), self.rx1_probe)
        self.connect(self.rx2_source, blocks.complex_to_mag_squared(), self.rx2_probe)

        # Path RX1 -> TX
        self.rx1_to_tx = blocks.multiply_const_cc(1)

        # Path RX2 -> TX
        self.rx2_to_tx = blocks.multiply_const_cc(1)

        # MUX to control which signal goes to the transmitter
        self.signal_mux = blocks.selector(gr.sizeof_gr_complex, 0, 0)

        # Connect RX1 and RX2 paths to the MUX
        self.connect(self.rx1_source, self.rx1_to_tx, (self.signal_mux, 0))
        self.connect(self.rx2_source, self.rx2_to_tx, (self.signal_mux, 1))

        # MUX output to transmitter
        self.connect(self.signal_mux, self.tx_sink)

    def start_relay(self):
        self.start()
        print("Relay started")

        last_detected_signal = ""

        def print_dynamic(rx1_power, rx2_power, detected_signal):
            print(f"\rRX1 Power: {rx1_power:.10f}, RX2 Power: {rx2_power:.10f}, {detected_signal}", end='')

        try:
            while True:
                # Monitor signal power on both RX paths
                rx1_power = self.rx1_probe.level()  # Get RX1 power level
                rx2_power = self.rx2_probe.level()  # Get RX2 power level

                detected_signal = last_detected_signal

                if rx1_power > 0.05:  # Adjust threshold for RX1 detection
                    detected_signal = "RX1 signal detected. Transmitting on TX1 frequency."
                    self.signal_mux.set_input_index(0)  # Route RX1 to TX
                    self.tx_sink.set_center_freq(self.tx1_freq)  # Set TX to match RX1 frequency
                    last_detected_signal = detected_signal

                elif rx2_power > 0.05:  # RX2 detection threshold
                    detected_signal = "RX2 signal detected. Transmitting on TX2 frequency."
                    self.signal_mux.set_input_index(1)  # Route RX2 to TX
                    self.tx_sink.set_center_freq(self.tx2_freq)  # Set TX to match RX2 frequency
                    last_detected_signal = detected_signal

                print_dynamic(rx1_power, rx2_power, detected_signal)
                time.sleep(0.1)  # Adjust frequency switch delay as needed

        except KeyboardInterrupt:
            print("Stopping relay...")
            self.stop()
            self.wait()

if __name__ == "__main__":
    parser = OptionParser(usage="usage: %prog [options]", description="Dynamic frequency relay for two receivers and one transmitter")
    parser.add_option("--rx1-freq", type="float", help="Receiver 1 frequency in Hz", metavar="FREQ")
    parser.add_option("--tx1-freq", type="float", help="Transmitter 1 frequency in Hz", metavar="FREQ")
    parser.add_option("--rx2-freq", type="float", help="Receiver 2 frequency in Hz", metavar="FREQ")
    parser.add_option("--tx2-freq", type="float", help="Transmitter 2 frequency in Hz", metavar="FREQ")
    parser.add_option("--rx1-args", type="string", default="rtl=0", help="Receiver 1 args (RTL-SDR)")
    parser.add_option("--rx2-args", type="string", default="bladerf=0", help="Receiver 2 args (BladeRF)")
    parser.add_option("--tx-args", type="string", default="bladerf=0", help="Transmitter args (BladeRF)")
    parser.add_option("-S", "--sample-rate", type="int", default=2400000, help="Sample rate in samples per second")
    # Example w/ command line parameters // generic VHF and UHF freqs input as placeholders // Only transmit on freqs you are licensed for 
    # python repeater.py --rx1-args "rtl=0" --rx1-freq [150.000e6] --rx2-args "bladerf=0" --rx2-freq [450.000e6] --tx-args "bladerf=0" --tx1-freq [450.000e6] --tx2-freq [150.000e6]

    (options, args) = parser.parse_args()

    if not (options.rx1_freq and options.tx1_freq and options.rx2_freq and options.tx2_freq):
        parser.print_help()
        exit(1)

    relay = dynamic_relay(
        rx1_freq=options.rx1_freq, tx1_freq=options.tx1_freq,
        rx2_freq=options.rx2_freq, tx2_freq=options.tx2_freq,
        rx1_args=options.rx1_args, rx2_args=options.rx2_args,
        tx_args=options.tx_args, sample_rate=options.sample_rate
    )

    relay.start_relay()
