import time

import cv2
from rich import print  # noqa: A004

from pupil_labs.realtime_api.simple import discover_one_device


def set_state_1(device, camera_state):
    print("Updating camera to state 1")
    device.set_camera_state(
        ae_mode="manual",
        man_exp=500,
        gain=64,
        brightness=0,
        contrast=32,
        gamma=300,
        validate_with_state=camera_state,
    )


def set_state_2(device, camera_state):
    print("Updating camera to state 2")
    device.set_camera_state(
        ae_mode="manual",
        man_exp=1000,
        gain=75,
        brightness=-20,
        contrast=50,
        gamma=200,
        validate_with_state=camera_state,
    )


def main():
    print("Looking for the next best device...")
    device = discover_one_device(max_search_duration_seconds=10)
    if device is None:
        print("No device found.")
        raise SystemExit(-1)

    # Initiate video stream before querying camera state to ensure camera is active
    # You could instead simply open the scene video preview in the companion app
    device.receive_scene_video_frame()

    print("Retrieving camera state...")
    camera_state = device.get_camera_state()
    print(f"Current camera state: {camera_state}")

    set_state_1(device, camera_state)
    last_state = 1
    last_tick_time = time.time()
    while True:
        bgr_pixels, frame_datetime = device.receive_scene_video_frame()
        draw_time(bgr_pixels, frame_datetime)
        cv2.imshow("Scene Camera - Press ESC to quit", bgr_pixels)

        if time.time() - last_tick_time > 4:
            if last_state == 1:
                set_state_2(device, camera_state)
                last_state = 2
            else:
                set_state_1(device, camera_state)
                last_state = 1
            last_tick_time = time.time()

        if cv2.waitKey(1) & 0xFF == 27:
            break

    device.close()


def draw_time(frame, timestamp):
    frame_txt_font_name = cv2.FONT_HERSHEY_SIMPLEX
    frame_txt_font_scale = 1.0
    frame_txt_thickness = 1

    # first line: frame index
    frame_txt = str(timestamp)

    cv2.putText(
        frame,
        frame_txt,
        (20, 50),
        frame_txt_font_name,
        frame_txt_font_scale,
        (255, 255, 255),
        thickness=frame_txt_thickness,
        lineType=cv2.LINE_8,
    )


if __name__ == "__main__":
    main()
