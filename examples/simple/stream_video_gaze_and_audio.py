import time

import cv2
import numpy as np

from ..audio_player import AudioPlayer

# Workaround for https://github.com/opencv/opencv/issues/21952
cv2.imshow("cv/av bug", np.zeros(1))
cv2.destroyAllWindows()

from pupil_labs.realtime_api.simple import discover_one_device  # noqa: E402

# NOTE: Audio playback is done in a separate process with SoundDevice and a circular
# buffer to avoid blocking the main thread and ensure smooth playback.
# An AudioPlayer class is provided in the realtime_api package for this purpose.


def main():
    # Look for devices. Returns as soon as it has found the first device.
    print("Looking for the next best device...")
    device = discover_one_device(max_search_duration_seconds=10)
    if device is None:
        print("No device found.")
        raise SystemExit(-1)

    print(f"Connecting to {device}...")
    player = AudioPlayer(samplerate=8000, channels=1, dtype="int16")
    try:
        player.start()
        time.sleep(1)  # Give some time to the player to start
        while True:
            matched = device.receive_matched_scene_video_frame_and_audio(
                timeout_seconds=5
            )
            if matched is None:
                continue

            frame, audio, gaze = matched

            # We add all audio frames to the player's queue
            for audio_frame in audio:
                player.add_data(next(audio_frame.to_resampled_ndarray()).T)

            # We display the number of audio frames received with the video frame
            if audio:
                cv2.putText(
                    frame.bgr_pixels,
                    f"Audio frames: {len(audio)}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )
            else:
                cv2.putText(
                    frame.bgr_pixels,
                    "No audio",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                )
            if gaze:
                cv2.circle(
                    frame.bgr_pixels,
                    (int(gaze.x), int(gaze.y)),
                    radius=80,
                    color=(0, 0, 255),
                    thickness=15,
                )
            cv2.imshow("Scene camera and audio", frame.bgr_pixels)
            if cv2.waitKey(1) & 0xFF == 27:
                break
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping...")
        player.close()
        device.close()  # explicitly stop auto-update


if __name__ == "__main__":
    main()
