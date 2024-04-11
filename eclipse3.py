from sigma_ptpy import SigmaPTPy
from sigma_ptpy.schema import CamDataGroup4, CamDataGroup2, CamDataGroup3, CamDataGroup1, CamDataGroupFocus, SnapCommand
from sigma_ptpy.enum import CaptStatus, DestToSave, ExposureMode, FocusMode, ImageQuality, ColorSpace, CaptureMode
from sigma_ptpy.apex import ShutterSpeed2Converter, ShutterSpeed3Converter, Aperture3Converter, ISOSpeedConverter, ExpComp3Converter
import time
import datetime

def wait_completion(camera, image_id):
    for _ in range(10000):
        status = camera.get_cam_capt_status(image_id)
        print(f" shooting: status={status.CaptStatus}")

        if status.CaptStatus in [CaptStatus.ImageGenCompleted, CaptStatus.ImageDataStorageCompleted]:
            return status
        elif status.CaptStatus in [CaptStatus.ShootInProgress, CaptStatus.ShootSuccess,
                                   CaptStatus.ImageGenInProgress, CaptStatus.AFSuccess,
                                   CaptStatus.CWBSuccess]:
            print(f"Waiting to complete shooting: status={status.CaptStatus}")
            time.sleep(0.1)
        else:
            print(f"Failed shooting: status={status.CaptStatus}")
            break

def take_photo(camera, shutter_speed, aperture):
    # Trigger camera to take a photo
    camera.snap_command(SnapCommand(0x02, 0x01))


    # Wait for the photo to be processed and stored
    status = wait_completion(camera, 0)
    if status:
        # Retrieve information about the last photo taken
        info = camera.get_pict_file_info2()
        print(info)
        save_last_photo(camera, info)

        camera.clear_image_db_single(status.ImageId)

def save_last_photo(camera, info):
    # Fetch the photo data
    pict = camera.get_big_partial_pict_file(info.FileAddress, 0, info.FileSize)
    # Format the filename with the current timestamp and the shutter_speed
    filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.dng")
    with open(filename, "wb") as fout:
        fout.write(pict.PartialData)
        print(f"A picture is saved as {filename}.")
def get_camera_data(camera):

    d1 = camera.get_cam_data_group1()

    print("CamDataGroup1:")
    if d1.ShutterSpeed is not None:
        ss = ShutterSpeed3Converter.decode_uint8(d1.ShutterSpeed)
        print(f"  ShutterSpeed = {ss} (%#02x)" % d1.ShutterSpeed)
    if d1.Aperture is not None:
        ec = Aperture3Converter.decode_uint8(d1.Aperture)
        print(f"  Aperture = {ec} (%#02x)" % d1.Aperture)
    if d1.ISOAuto is not None:
        print(f"  ISOAuto = {str(d1.ISOAuto)}")
    if d1.ISOSpeed is not None:
        iso = ISOSpeedConverter.decode_uint8(d1.ISOSpeed)
        print(f"  ISOSpeed = {iso} (%#02x)" % d1.ISOSpeed)
    if d1.ExpComp is not None:
        ec = ExpComp3Converter.decode_uint8(d1.ExpComp)
        print(f"  ExpCompensation = {ec} (%#02x)" % d1.ExpComp)
    if d1.ABValue is not None:
        ab = ExpComp3Converter.decode_uint8(d1.ExpComp)
        print(f"  ABValue = {ab} (%#02x)" % d1.ABValue)

def take_one_photo(camera, shutter_speed, aperture):

    camera.config_api()
    # get_camera_data(camera)

    # Print out the details of the photo we're taking
    print(f"Taking photo with shutter speed {shutter_speed} and aperture {aperture}")
    take_photo(camera, shutter_speed, aperture)

    camera.close_application()

import time

def take_photos_over_ranges():

    end_time = time.time() + 30 * 60  # 30 minutes from now
    camera = SigmaPTPy(ignore_events=True)

    camera.config_api()
    apertures = [ 11]
    shutter_speeds = [122]
#    shutter_speeds = [1/500, 1/2000, 1/8000]

    while time.time() < end_time:
        with camera.session():
            for aperture in apertures:
                for shutter_speed in shutter_speeds:
                    camera.set_cam_data_group_focus(CamDataGroupFocus(FocusMode=FocusMode.MF))
                    camera.set_cam_data_group2(CamDataGroup2(ImageQuality=ImageQuality.DNG, ExposureMode=ExposureMode.Manual))
                    camera.set_cam_data_group3(CamDataGroup3(DestToSave=0x02))
# camera.set_cam_data_group3(CamDataGroup3("0300800386"))
                    camera.set_cam_data_group4(CamDataGroup4(ShutterSound=1))
                    # camera.set_cam_data_group1(CamDataGroup1(ShutterSpeed=ShutterSpeed3Converter.encode_uint8(shutter_speed), ISOSpeed=0x01, ISOAuto=0x00, Aperture=Aperture3Converter.encode_uint8(aperture ) ))
                    camera.set_cam_data_group1(CamDataGroup1(ShutterSpeed=shutter_speed, ISOSpeed=0x01, ISOAuto=0x00, Aperture=Aperture3Converter.encode_uint8(aperture ) ))

                    camera.set_cam_data_group3(CamDataGroup3(DestToSave=0x01))

                    take_one_photo(camera, shutter_speed, aperture)
        time.sleep(5)
if __name__ == '__main__':
    take_photos_over_ranges()
