from collections import deque

import sounddevice as sd

from pupil_labs.realtime_api.simple import discover_one_device


def main():
    # Look for devices. Returns as soon as it has found the first device.
    print("Looking for the next best device...")
    device = discover_one_device(max_search_duration_seconds=10)
    if device is None:
        print("No device found.")
        raise SystemExit(-1)
    print(f"Found device: {device}")
    device.streaming_start(
        "audio"
    )  # optional, if not called, stream is started on-demand
    stream = None
    buf = deque()
    try:
        while True:
            audio_frame = device.receive_audio_frame(timeout_seconds=5)
            if audio_frame:
                buf.append(next(audio_frame.to_resampled_ndarray()).T)
                if not stream:
                    # Initialize the player with the correct parameters from first frame
                    stream = sd.OutputStream(
                        samplerate=audio_frame.av_frame.sample_rate,
                        channels=audio_frame.av_frame.layout.nb_channels,
                        dtype="int16",
                        blocksize=0,  # Let the device choose the optimal size for low latency  # noqa: E501
                        latency="low",
                    )
                    # Start the player process
                    stream.start()
                    print(
                        f"Audio stream parameters: "
                        f"Sample Rate: {audio_frame.av_frame.sample_rate}, "
                        f"Channels: {audio_frame.av_frame.layout.nb_channels}, "
                        f"Layout: {audio_frame.av_frame.layout.name}"
                    )
                    print("Started audio playback.")

                while buf:
                    stream.write(buf.popleft())

    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping...")
        # device.streaming_stop()  # optional, if not called, stream is stopped on close
        device.close()  # explicitly stop auto-update
        if stream:
            stream.close()


if __name__ == "__main__":
    main()
