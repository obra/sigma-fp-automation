import usb.core
import usb.util
import struct

# Find the camera device
dev = usb.core.find(idVendor=0x1003, idProduct=0xc432)

if dev is None:
    raise ValueError('Camera device not found')

# Set the active configuration
dev.set_configuration()

# Get an endpoint instance
cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]

ep = usb.util.find_descriptor(
    intf,
    custom_match= \
    lambda e: \
        usb.util.endpoint_direction(e.bEndpointAddress) == \
        usb.util.ENDPOINT_IN)

assert ep is not None

# Send the PTP2 command to take a photo
cmd_packet = struct.pack(
    '<BHHHH',
    0x02, 0x00, 0x00, 0x00, 0x0C
)
cmd_packet += b'\x00\x00\x00\x01\x00\x00\x00\x00'

# Send the command packet
dev.ctrl_transfer(
    usb.util.build_request_type(
        usb.util.CTRL_OUT,
        usb.util.CTRL_TYPE_CLASS,
        usb.util.CTRL_RECIPIENT_INTERFACE
    ),
    0x00,
    0x00, 0x00,
    cmd_packet
)

# Read the response packet
response = dev.read(ep.bEndpointAddress, ep.wMaxPacketSize)

# Check the response status
if response[2] != 0x20:
    print(f'Error taking photo: {response[2]}')
else:
    print('Photo taken successfully!')
