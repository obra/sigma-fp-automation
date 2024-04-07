import usb.core
import usb.util
import struct

# Sigma fp camera vendor and product IDs
VENDOR_ID = 0x1003
PRODUCT_ID = 0xc432

# Custom operation codes
SNAP_COMMAND = 0x901b
GET_CAM_CAPT_STATUS = 0x9015
GET_PICT_FILE_INFO_2 = 0x902d
GET_BIG_PARTIAL_PICT_FILE = 0x9022
CLEAR_IMAGE_DB_SINGLE = 0x901c

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

    # Send the snap command
    send_command(dev, SNAP_COMMAND, data=b'\x02\x02\x01\x05')

    # Get the capture status
    while True:
        status = get_capture_status(dev)
        if status[2] == 0x05:
            break

    # Get the picture file info
    file_info = get_picture_file_info(dev)
    file_size = struct.unpack('<I', file_info[8:12])[0]

    # Get the picture file data
    file_data = get_picture_file_data(dev, file_size)

    # Save the picture file
    with open('captured_photo.jpg', 'wb') as f:
        f.write(file_data)

    # Clear the image from the camera
    clear_image(dev)

def send_command(dev, opcode, param1=0, param2=0, data=None):
    if data is None:
        data = b''
    packet = struct.pack('<IIII', opcode, param1, param2, len(data)) + data
    dev.write(0x01, packet)

def get_response(dev):
    response = dev.read(0x83, 1024)
    opcode, _, _, data_len = struct.unpack('<IIII', response[:16])
    data = response[16:16+data_len]
    return opcode, data

def get_capture_status(dev):
    send_command(dev, GET_CAM_CAPT_STATUS, param1=1)
    _, data = get_response(dev)
    return data

def get_picture_file_info(dev):
    send_command(dev, GET_PICT_FILE_INFO_2)
    _, data = get_response(dev)
    return data

def get_picture_file_data(dev, file_size):
    file_data = b''
    offset = 0
    while offset < file_size:
        chunk_size = min(file_size - offset, 0x10000)
        send_command(dev, GET_BIG_PARTIAL_PICT_FILE, param1=offset, param2=chunk_size)
        _, data = get_response(dev)
        file_data += data
        offset += chunk_size
    return file_data

def clear_image(dev):
    send_command(dev, CLEAR_IMAGE_DB_SINGLE, param1=1)

if __name__ == "__main__":
    capture_photo()
