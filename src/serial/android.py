from usb4a import usb
from usbserial4a import serial4a

class Serial:

    @staticmethod
    def get_devices():
        usb_devices = usb.get_usb_device_list()
        device_names = [device.getDeviceName() for device in usb_devices]
        return device_names

    @staticmethod
    def connect(device):
        return serial4a.get_serial_port(
            device,
            115200,   # Baudrate
            8,      # Number of data bits(5, 6, 7 or 8)
            'N',    # Parity('N', 'E', 'O', 'M' or 'S')
            1, # Number of stop bits(1, 1.5 or 2)
        )
