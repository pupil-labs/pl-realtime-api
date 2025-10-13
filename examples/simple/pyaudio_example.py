import cv2
import numpy as np
import pyaudio

# Workaround for https://github.com/opencv/opencv/issues/21952
cv2.imshow("cv/av bug", np.zeros(1))
cv2.destroyAllWindows()

from pupil_labs.realtime_api.simple import discover_one_device  # noqa: E402


def main():
    """Connect to a device, receive data, and play audio."""
    print("Looking for the next best device...")
    device = discover_one_device(max_search_duration_seconds=10)
    if device is None:
        print("No device found.")
        raise SystemExit(-1)

    print(f"Connecting to {device}...")

    p = pyaudio.PyAudio()

    SAMPLE_RATE = 8000
    CHANNELS = 1
    FORMAT = pyaudio.paFloat32

    stream = p.open(format=FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, output=True)

    try:
        while True:
            matched = device.receive_matched_scene_video_frame_and_audio(
                timeout_seconds=5
            )
            if matched is None:
                continue

            frame, audio, gaze = matched

            for audio_frame in audio:
                stream.write(audio_frame.to_ndarray().tobytes())

            time_diff_ms = [
                frame.timestamp_unix_seconds - af.timestamp_unix_seconds for af in audio
            ]

            # Display status text on the video frame
            if audio:
                cv2.putText(
                    frame.bgr_pixels,
                    (
                        f"Audio frames: {len(audio)} (float32) / "
                        f"Mean diff: {np.mean(time_diff_ms) * 1000:.0f} ms"
                    ),
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )
            else:
                cv2.putText(
                    frame.bgr_pixels,
                    "No audio received",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                )

            # Draw the gaze point on the frame
            if gaze:
                cv2.circle(
                    frame.bgr_pixels,
                    (int(gaze.x), int(gaze.y)),
                    radius=80,
                    color=(0, 0, 255),
                    thickness=15,
                )

            # Show the video frame
            cv2.imshow("Scene Camera with PyAudio Playback (float32)", frame.bgr_pixels)

            if cv2.waitKey(1) & 0xFF == 27:
                break
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        if device:
            device.close()


if __name__ == "__main__":
    main()
