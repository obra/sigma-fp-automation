import usb.core
import usb.util
import struct
import time

# PTP Command Codes (Generic)
PTP_OC_OpenSession = 0x1002
PTP_OC_CloseSession = 0x1003
PTP_OC_InitiateCapture = 0x100E

# Replace with your camera's vendor and product IDs
VENDOR_ID = 0x1003  # Example: Nikon
PRODUCT_ID = 0xc432  # Example: D90

# Find the camera
camera = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
if camera is None:
    raise ValueError('Camera not found')

# Detach the camera from the kernel driver
if camera.is_kernel_driver_active(0):
    camera.detach_kernel_driver(0)

# Set the active configuration to the first one
camera.set_configuration()

# Endpoint and interface setup
# These values may need to be adjusted for your specific camera
interface = 0
endpoint_out = 0x01  # Replace with your camera's OUT endpoint
endpoint_in = 0x81   # Replace with your camera's IN endpoint

# Function to send a PTP command
def send_ptp_command(command, data=[]):
    # PTP container structure: (length, type, code, transaction_id, parameters)
    container = struct.pack('<IHHI', 12 + len(data) * 4, 1, command, 1) + struct.pack('<' + 'I' * len(data), *data)
    camera.write(endpoint_out, container)

# Function to receive a PTP response
def receive_ptp_response():
    response = camera.read(endpoint_in, 512, timeout=5000)
    return response

# Open PTP session
send_ptp_command(PTP_OC_OpenSession, [1])
print("Session Opened")
time.sleep(1)  # Wait for the command to be processed

# Initiate capture
send_ptp_command(PTP_OC_InitiateCapture, [0xFFFFFFFF, 0x0000])
print("Capture Initiated")
time.sleep(1)  # Wait for the capture to complete

# Close PTP session
send_ptp_command(PTP_OC_CloseSession)
print("Session Closed")

# Release the camera
usb.util.dispose_resources(camera)
