import usb.core
import usb.util
import struct
import time

# PTP2 Command Codes (Generic)
PTP_OC_OpenSession = 0x1002
PTP_OC_CloseSession = 0x1003
PTP_OC_InitiateCapture = 0x901B #  0x100E

# Replace with your camera's vendor and product IDs
VENDOR_ID = 0x1003  # Example ID, replace with your camera's vendor ID
PRODUCT_ID = 0xc432  # Example ID, replace with your camera's product ID

# Initialize global transaction ID
transaction_id = 1

# Find the camera
camera = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
if camera is None:
    raise ValueError('Camera not found')

# Detach the camera from the kernel driver
if camera.is_kernel_driver_active(0):
    camera.detach_kernel_driver(0)

# Set the active configuration. Assuming first configuration is relevant.
camera.set_configuration()

# Claim the interface
interface = 0
usb.util.claim_interface(camera, interface)

cfg = camera.get_active_configuration()
intf = cfg[(0,0)]  # Assuming first interface and first setting; adjust as necessary

for ep in intf:
    print(ep.bEndpointAddress, usb.util.endpoint_direction(ep.bEndpointAddress))

# Endpoint addresses - Replace with your camera's specific endpoints
endpoint_out = 0x01
endpoint_in = 0x83

def send_ptp_command(command, data=[]):
    global transaction_id
    # PTP container structure: (length, type, code, transaction_id, parameters)
    container_length = 12 + len(data) * 4
    container = struct.pack('<IHHI', container_length, 1, command, transaction_id)
    if data:
        container += struct.pack('<' + 'I' * len(data), *data)
    camera.write(endpoint_out, container)
    transaction_id += 1

def receive_ptp_response():
    # Assuming response does not exceed 512 bytes
    response = camera.read(endpoint_in, 512, timeout=5000)
    return response

# Open PTP session
send_ptp_command(PTP_OC_OpenSession, [1])
response = receive_ptp_response()
print("Session Opened", response)

# Give the camera a moment to process
time.sleep(1)

# Trigger an image capture
send_ptp_command(PTP_OC_InitiateCapture, [0xFFFFFFFF, 0x0000])
response = receive_ptp_response()
print("Capture Initiated", response)

# Close the session
send_ptp_command(PTP_OC_CloseSession)
response = receive_ptp_response()
print("Session Closed", response)

# Release the device
usb.util.release_interface(camera, interface)
usb.util.dispose_resources(camera)

