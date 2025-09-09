import asyncio
import contextlib
import logging
import threading
import typing as T
from queue import Empty, Queue

import numpy as np
import numpy.typing as npt

try:
    import sounddevice as sd
except ImportError:
    print(
        "Sounddevice library not found. Please install with: pip install sounddevice to"
        "run this example or install pl-realtime with examples extras: "
        "pip install pl-realtime[examples]"
    )
    exit()

from pupil_labs.realtime_api import (
    AudioFrame,
    Device,
    Network,
    receive_audio_frames,
)

logging.basicConfig(level=logging.INFO)

# Threading event to signal the audio playback thread to stop
stop_audio_event = threading.Event()


async def enqueue_audio_data(
    audio_generator: T.AsyncIterator[AudioFrame],
    audio_queue: Queue,
) -> None:
    """Gets audio frames from a generator resamples and puts them into a queue."""
    logging.info("Audio enqueuer task started.")
    try:
        async for audio_frame in audio_generator:
            # We place the resampled ndarray (s16) in the queue
            # for the audio callback to consume.
            for resampled_chunk in audio_frame.to_resampled_ndarray():
                audio_queue.put_nowait(resampled_chunk)
    except asyncio.CancelledError:
        logging.info("Audio enqueuer task cancelled.")
    except Exception:
        logging.exception("An error occurred in the audio enqueuer task.")
    finally:
        logging.info("Audio enqueuer task finished. Signaling end of stream.")
        audio_queue.put(None)  # Signal end of stream to the consumer


def audio_playback_thread_target(
    sample_rate: int,
    channels: int,
    stop_event: threading.Event,
    audio_queue: Queue,
):
    """Dedicated thread for sounddevice playback.

    This runs in a separate thread to avoid blocking the main asyncio event loop.
    """
    logging.info("Audio playback thread started.")
    audio_buffer = np.array([], dtype=np.int16)

    def audio_callback(
        outdata: npt.NDArray[np.int16],
        frames: int,
        time_info: T.Any,
        status: sd.CallbackFlags,
    ):
        """The callback function for the audio stream playback."""
        nonlocal audio_buffer
        if status:
            logging.warning(f"Audio stream status: {status}")
        while len(audio_buffer) < frames:
            try:
                chunk = audio_queue.get_nowait()
                if chunk is None:
                    logging.info("End of stream signal received in callback.")
                    raise sd.CallbackStop("End of stream.")
                audio_buffer = np.concatenate((audio_buffer, chunk.flatten()))
            except Empty:
                logging.debug("Audio buffer underrun: filling with silence.")
                break

        frames_to_play = audio_buffer[:frames]
        audio_buffer = audio_buffer[frames:]

        outdata[: len(frames_to_play), 0] = frames_to_play
        if len(frames_to_play) < frames:
            outdata[len(frames_to_play) :, 0] = 0

    try:
        stream = sd.OutputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            callback=audio_callback,
            blocksize=0,
            latency="low",
        )
        with stream:
            logging.info("Audio stream started")
            stop_event.wait()  # Wait until the main thread signals to stop
            logging.info("Stop signal received, closing audio stream.")
    except Exception:
        logging.exception("An error occurred in the audio playback thread.")
    finally:
        logging.info("Audio playback thread finished.")


async def main():
    audio_queue: Queue[np.ndarray | None] = Queue(maxsize=10)

    try:
        async with Network() as network:
            dev_info = await network.wait_for_new_device(timeout_seconds=5)
            if dev_info is None:
                print("No device could be found! Aborting.")
                return

            async with Device.from_discovered_device(dev_info) as device:
                print(f"Connecting to {device}...")
                status = await device.get_status()

                sensor_audio = status.direct_audio_sensor()
                if not sensor_audio.connected:
                    print(f"Audio sensor is not connected to {device}. Aborting.")
                    return

                audio_generator = receive_audio_frames(sensor_audio.url, run_loop=True)

                first_frame = await anext(audio_generator)
                sample_rate = first_frame.av_frame.sample_rate
                channels = first_frame.av_frame.layout.nb_channels
                print(
                    f"Audio stream parameters: "
                    f"Sample Rate: {sample_rate}, "
                    f"Channels: {channels}, "
                    f"Layout: {first_frame.av_frame.layout.name}"
                )

                audio_playback_thread = threading.Thread(
                    target=audio_playback_thread_target,
                    args=(
                        sample_rate,
                        channels,
                        stop_audio_event,
                        audio_queue,  # Pass the queue to the thread
                    ),
                    name="AudioPlaybackThread",
                )
                audio_playback_thread.start()

                # Start the asyncio task to enqueue audio data from the generator
                enqueue_task = asyncio.create_task(
                    enqueue_audio_data(audio_generator, audio_queue)
                )

                # Prime the queue with the first frame we already extracted
                for resampled_chunk in first_frame.to_resampled_ndarray():
                    audio_queue.put_nowait(resampled_chunk)

                # Wait for the enqueuer task to complete or be cancelled
                await enqueue_task

    except asyncio.CancelledError:
        logging.info("Main task cancelled.")
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received, initiating shutdown.")
    finally:
        logging.info("Cleaning up resources...")
        # The 'async with' blocks will handle device disconnection automatically.
        # We just need to manage our custom thread.
        if "audio_playback_thread" in locals() and audio_playback_thread.is_alive():
            stop_audio_event.set()  # Signal the audio playback thread to stop
            audio_playback_thread.join(timeout=5)  # Wait for the thread to finish
            if audio_playback_thread.is_alive():
                logging.warning("Audio playback thread did not terminate cleanly.")
        logging.info("Cleanup complete.")


if __name__ == "__main__":
    # Use contextlib.suppress to avoid a traceback on KeyboardInterrupt
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
