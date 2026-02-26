import cv2
import numpy as np

# Workaround for https://github.com/opencv/opencv/issues/21952
cv2.imshow("cv/av bug", np.zeros(1))
cv2.destroyAllWindows()

from pupil_labs.realtime_api.simple import discover_one_device  # noqa: E402
from pupil_labs.realtime_api.streaming.gaze import (  # noqa: E402
    BinoAndDualMonoGazeData,
    EyestateEyelidDualMonoGazeData,
)

LEGEND = {
    "mono_right": (255, 0, 0),  # right eye monocular gaze
    "mono_left": (0, 255, 0),  # left eye monocular gaze
    "bino": (0, 0, 255),  # binocular gaze
}


def main():
    # Look for devices. Returns as soon as it has found the first device.
    print("Looking for the next best device...")
    device = discover_one_device(max_search_duration_seconds=10)
    if device is None:
        print("No device found.")
        raise SystemExit(-1)

    print(f"Connecting to {device}...")

    try:
        while True:
            frame, gaze = device.receive_matched_scene_video_frame_and_gaze()
            cv2.circle(
                frame.bgr_pixels,
                (int(gaze.x), int(gaze.y)),
                radius=40,
                color=(0, 0, 255),
                thickness=5,
            )
            if isinstance(
                gaze, (BinoAndDualMonoGazeData, EyestateEyelidDualMonoGazeData)
            ):
                cv2.circle(
                    frame.bgr_pixels,
                    (int(gaze.mono_right_x), int(gaze.mono_right_y)),
                    radius=40,
                    color=(255, 0, 0),
                    thickness=5,
                )
                cv2.circle(
                    frame.bgr_pixels,
                    (int(gaze.mono_left_x), int(gaze.mono_left_y)),
                    radius=40,
                    color=(0, 255, 0),
                    thickness=5,
                )
                for eye, color in LEGEND.items():
                    cv2.rectangle(
                        frame.bgr_pixels,
                        (10, 10 + 30 * list(LEGEND.keys()).index(eye)),
                        (30, 30 + 30 * list(LEGEND.keys()).index(eye)),
                        color,
                        -1,
                    )
                    cv2.putText(
                        frame.bgr_pixels,
                        eye,
                        (40, 30 + 30 * list(LEGEND.keys()).index(eye)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        1,
                        cv2.LINE_AA,
                    )

            cv2.imshow("Scene camera with gaze overlay", frame.bgr_pixels)
            if cv2.waitKey(1) & 0xFF == 27:
                break
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping...")
        device.close()  # explicitly stop auto-update


if __name__ == "__main__":
    main()
