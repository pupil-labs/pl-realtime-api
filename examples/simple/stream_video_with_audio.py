import cv2
import numpy as np
import sounddevice as sd

# Workaround for https://github.com/opencv/opencv/issues/21952
cv2.imshow("cv/av bug", np.zeros(1))
cv2.destroyAllWindows()

from pupil_labs.realtime_api.simple import discover_one_device  # noqa: E402


def main():
    # Look for devices. Returns as soon as it has found the first device.
    print("Looking for the next best device...")
    device = discover_one_device(max_search_duration_seconds=10)
    if device is None:
        print("No device found.")
        raise SystemExit(-1)

    print(f"Connecting to {device}...")

    # Open a sounddevice stream
    audio_sensor = device.audio_sensor()
    sd.default.samplerate = audio_sensor.frequency
    sd.default.channels = audio_sensor.channels

    try:
        with sd.OutputStream() as stream:
            while True:
                matched = device.receive_matched_scene_video_frame_and_audio()
                if matched is None:
                    continue

                frame, audio = matched

                for audio_frame in audio:
                    stream.write(audio_frame.to_ndarray())

                cv2.imshow("Scene camera", frame.bgr_pixels)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping...")
        device.close()  # explicitly stop auto-update


if __name__ == "__main__":
    main()
