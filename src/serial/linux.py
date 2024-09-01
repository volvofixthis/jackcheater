import serial
import glob

class Serial:

    @staticmethod
    def get_devices():
        return glob.glob("/dev/tty*")

    @staticmethod
    def connect(device):
        return serial.Serial(device, 115200)
