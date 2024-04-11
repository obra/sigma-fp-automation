import subprocess
import time
import datetime
from sigma_ptpy import SigmaPTPy
from sigma_ptpy.schema import CamDataGroup4, CamDataGroup2, CamDataGroup3, CamDataGroup1, CamDataGroupFocus, SnapCommand
from sigma_ptpy.enum import CaptStatus, DestToSave, ExposureMode, FocusMode, ImageQuality, ColorSpace, CaptureMode
from sigma_ptpy.apex import ShutterSpeed2Converter, Aperture3Converter

def play_sound(message):
    # Use macOS 'say' command to play a sound notification with a message
    subprocess.run(['say', message])

def wait_completion(camera, image_id):
    for _ in range(10000):
        status = camera.get_cam_capt_status(image_id)
        if status.CaptStatus in [CaptStatus.ImageGenCompleted, CaptStatus.ImageDataStorageCompleted]:
            return status
        elif status.CaptStatus in [CaptStatus.ShootInProgress, CaptStatus.ShootSuccess, CaptStatus.ImageGenInProgress, CaptStatus.AFSuccess, CaptStatus.CWBSuccess]:
            time.sleep(0.1)
        else:
            break

def take_photo(camera, shutter_speed, aperture):
    camera.snap_command(SnapCommand(0x02, 0x01))
    camera.set_cam_data_group_focus(CamDataGroupFocus(FocusMode=FocusMode.MF))
    camera.set_cam_data_group2(CamDataGroup2(ImageQuality=ImageQuality.DNG, ExposureMode=ExposureMode.Manual))
    camera.set_cam_data_group3(CamDataGroup3(DestToSave=0x02))
    camera.set_cam_data_group4(CamDataGroup4(ShutterSound=1))
    camera.set_cam_data_group1(CamDataGroup1(ShutterSpeed=ShutterSpeed2Converter.encode_uint8(shutter_speed), ISOSpeed=0x01, ISOAuto=0x00, Aperture=Aperture3Converter.encode_uint8(aperture)))
    status = wait_completion(camera, 0)
    if status:
        info = camera.get_pict_file_info2()
        save_last_photo(camera, info)
        camera.clear_image_db_single(status.ImageId)

def save_last_photo(camera, info):
    pict = camera.get_big_partial_pict_file(info.FileAddress, 0, info.FileSize)
    filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.dng")
    with open(filename, "wb") as fout:
        fout.write(pict.PartialData)
        print(f"A picture is saved as {filename}.")

def take_photos_during_eclipse(camera):
    c1_time = datetime.datetime(2024, 4, 8, 12, 17, 26)
    c2_time = datetime.datetime(2024, 4, 8, 13, 34, 53)
    totality_duration = datetime.timedelta(seconds=260.4)
    end_totality_time = c2_time + totality_duration
    end_time = c1_time + datetime.timedelta(minutes=120)  # Continue shooting for 120 minutes after C1

    # Adjust for the specifics of your shooting scenario
    aperture = 8  # Example aperture; adjust as needed

    pre_totality_shutter_speeds = [ 1/2000, 1/800, 1/250]  # Before totality
    totality_shutter_speeds = [1/8, 1/15, 1/30, 1/60, 1/250]  # During totality
    post_totality_shutter_speeds = pre_totality_shutter_speeds[::-1]  # After totality, reverse of pre

    camera.config_api()
    with camera.session():
        play_sound("Add solar filter now")
        while c1_time <= datetime.datetime.now() < c2_time:
            for shutter_speed in pre_totality_shutter_speeds:
                take_photo(camera, shutter_speed, aperture)
            time.sleep(10)  # Shot duration + buffer

        play_sound("Remove solar filter now")
        while c2_time <= datetime.datetime.now() <= end_totality_time:
            for shutter_speed in totality_shutter_speeds:
                take_photo(camera, shutter_speed, aperture)
            time.sleep(1)  # Adjust based on desired frequency

        play_sound("Add solar filter now")
        while end_totality_time < datetime.datetime.now() <= end_time:
            for shutter_speed in post_totality_shutter_speeds:
                take_photo(camera, shutter_speed, aperture)
            time.sleep(10)  # Adjust based on desired frequency

if __name__ == '__main__':
    camera = SigmaPTPy(ignore_events=True)
    take_photos_during_eclipse(camera)
