import usb.core
import usb.util
import struct
import time

# Sigma fp camera vendor and product IDs
VENDOR_ID = 0x1003
PRODUCT_ID = 0xc432

# Endpoint addresses
OUT_EP = 0x01
IN_EP = 0x83

# PTP2 operation codes
INITIATE_CAPTURE = 0x100E
GET_DEVICE_INFO = 0x1001

def capture_photo():
    # Find the Sigma fp camera
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        raise ValueError("Sigma fp camera not found")

    # Detach the kernel driver if necessary
    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)

    # Set the configuration
    dev.set_configuration()

    # Get the device info
    response = send_ptp_command(dev, GET_DEVICE_INFO)
    print("Device info:", response)

    # Initiate capture
    send_ptp_command(dev, INITIATE_CAPTURE)

    # Poll the IN endpoint for the response
    response = None
    while response is None:
        try:
            response = dev.read(IN_EP, 1024, timeout=1000)
        except usb.core.USBError as e:
            if e.errno == 110:  # Operation timed out
                continue
            else:
                raise

    print("Capture response:", response)

def send_ptp_command(dev, operation, params=None):
    # Create the PTP2 command packet
    if params is None:
        params = []
    packet = struct.pack("<IHHI", len(params), operation, 0, 0)
    for param in params:
        packet += struct.pack("<I", param)

    # Send the command packet
    dev.write(OUT_EP, packet)

    # Read the response packet
    response = None
    while response is None:
        try:
            response = dev.read(IN_EP, 1024, timeout=1000)
        except usb.core.USBError as e:
            if e.errno == 110:  # Operation timed out
                continue
            else:
                raise

    return response

if __name__ == "__main__":
    capture_photo()
