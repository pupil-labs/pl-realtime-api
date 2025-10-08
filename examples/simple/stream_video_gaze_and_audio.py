import os
import sys

import cv2
import numpy as np

# Allow for absloute imports, to import audio_player from the parent directory.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from audio_player import AudioPlayer

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

            buffer_fill_ms = 1000 * player.get_buffer_size() / player.samplerate

            # We display the number of audio frames received with the video frame
            time_diff_ms = [
                frame.timestamp_unix_seconds - af.timestamp_unix_seconds for af in audio
            ]
            if audio:
                cv2.putText(
                    frame.bgr_pixels,
                    (
                        f"Audio frames: {len(audio)} / "
                        f"Buffer: {buffer_fill_ms:.0f} ms / "
                        f"Mean diff. audio-scene: {np.mean(time_diff_ms) * 1000:.0f} ms"
                    ),
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )
            else:
                cv2.putText(
                    frame.bgr_pixels,
                    f"No audio / Buffer: {buffer_fill_ms:.0f} ms",
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
