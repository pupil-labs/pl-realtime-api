import asyncio
import contextlib
import logging
import threading
import typing as T
from queue import Empty, Queue

import cv2
import numpy as np
import numpy.typing as npt
import sounddevice as sd

from pupil_labs.realtime_api import (
    Device,
    Network,
    receive_audio_frames,
    receive_gaze_data,
    receive_video_frames,
)

logging.basicConfig(level=logging.INFO)

# Use a threading event to signal the audio playback thread to stop
stop_audio_event = threading.Event()

# OpenCV workaround for a known issue
cv2.imshow("cv/av bug", np.zeros(1))
cv2.destroyAllWindows()


def audio_playback_thread_target(
    sample_rate: int,
    stop_event: threading.Event,
    audio_queue: Queue,
):
    """Dedicated thread for sounddevice playback.

    This runs in a separate thread to avoid blocking the main asyncio event loop.
    It receives raw AudioFrames, resamples them, and plays them back.
    """
    logging.info("Audio playback thread started.")
    audio_buffer = np.array([], dtype=np.int16)

    def audio_callback(outdata: npt.NDArray[np.int16], frames: int, *args):
        nonlocal audio_buffer
        while len(audio_buffer) < frames:
            try:
                frame = audio_queue.get_nowait()
                if frame is None:
                    raise sd.CallbackStop("End of stream.")
                for resampled_chunk in frame.to_resampled_ndarray():
                    audio_buffer = np.concatenate((
                        audio_buffer,
                        resampled_chunk.flatten(),
                    ))
            except Empty:
                logging.debug("Audio buffer underrun: filling with silence.")
                break

        frames_to_play = min(len(audio_buffer), frames)
        outdata[:frames_to_play, 0] = audio_buffer[:frames_to_play]
        outdata[frames_to_play:, 0] = 0
        audio_buffer = audio_buffer[frames_to_play:]

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
            logging.info("Audio stream started.")
            stop_event.wait()
            logging.info("Stop signal received, closing audio stream.")
    except Exception:
        logging.exception("An error occurred in the audio playback thread.")
    finally:
        logging.info("Audio playback thread finished.")


async def manage_audio_playback(
    queue_audio: asyncio.Queue, audio_playback_queue: Queue
):
    """Audio management task.

    Waits for the first audio frame, starts the playback thread,
    and then continuously moves frames from the asyncio queue to the thread's queue.
    """
    audio_playback_thread = None
    try:
        # Wait for the first frame to arrive to start the playback thread
        _ts, first_frame = await queue_audio.get()
        logging.info("First audio frame received, starting playback thread.")

        sample_rate = first_frame.av_frame.sample_rate
        audio_playback_thread = threading.Thread(
            target=audio_playback_thread_target,
            args=(sample_rate, stop_audio_event, audio_playback_queue),
            name="AudioPlaybackThread",
        )
        audio_playback_thread.start()

        # Put the first frame into the playback queue
        audio_playback_queue.put(first_frame)

        # Continuously move frames from the async queue to the playback queue
        while not stop_audio_event.is_set():
            _ts, frame = await queue_audio.get()
            audio_playback_queue.put(frame)

    except asyncio.CancelledError:
        logging.info("Audio manager task cancelled.")
    finally:
        if audio_playback_thread and audio_playback_thread.is_alive():
            # Signal end of stream to the audio thread
            audio_playback_queue.put(None)
        logging.info("Audio manager task finished.")


async def enqueue_sensor_data(sensor: T.AsyncIterator, queue: asyncio.Queue) -> None:
    """Move sensor data into an asyncio queue."""
    async for datum in sensor:
        try:
            queue.put_nowait((datum.datetime, datum))
        except asyncio.QueueFull:
            logging.warning(f"Queue is full, dropping {datum.__class__.__name__}")


async def get_most_recent_item(queue: asyncio.Queue):
    """Empty the queue and returns the last item."""
    item = await queue.get()
    while True:
        try:
            next_item = queue.get_nowait()
        except asyncio.QueueEmpty:
            return item
        else:
            item = next_item


async def get_closest_item(queue: asyncio.Queue, timestamp):
    """Get the item from the queue that is closest in time to the timestamp."""
    item_ts, item = await queue.get()
    if item_ts > timestamp:
        return item_ts, item
    while True:
        try:
            next_item_ts, next_item = queue.get_nowait()
        except asyncio.QueueEmpty:
            return item_ts, item
        else:
            if next_item_ts > timestamp:
                return next_item_ts, next_item
            item_ts, item = next_item_ts, next_item


async def match_and_draw(queue_video: asyncio.Queue, queue_gaze: asyncio.Queue):
    """Match video and gaze data and draws the gaze overlay."""
    while not stop_audio_event.is_set():
        try:
            video_datetime, video_frame = await get_most_recent_item(queue_video)
            _, gaze_datum = await get_closest_item(queue_gaze, video_datetime)

            bgr_buffer = video_frame.to_ndarray(format="bgr24")
            cv2.circle(
                bgr_buffer,
                (int(gaze_datum.x), int(gaze_datum.y)),
                radius=20,
                color=(0, 0, 255),
                thickness=5,
            )
            cv2.imshow("Scene Camera with Gaze and Audio", bgr_buffer)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("'q' pressed, exiting.")
                break
        except asyncio.QueueEmpty:
            # Queues might be empty at the start, just continue
            await asyncio.sleep(0.01)
            continue
        except Exception:
            logging.exception("Error in drawing loop")
            break


async def main():
    async with Network() as network:
        try:
            dev_info = await network.wait_for_new_device(timeout_seconds=5)
            if dev_info is None:
                logging.error("No device found. Aborting.")
                return
        except asyncio.TimeoutError:
            logging.exception("Timeout while searching for a device. Aborting.")
            return

        async with Device.from_discovered_device(dev_info) as device:
            logging.info(f"Connecting to {device}...")
            status = await device.get_status()

            sensor_world = status.direct_world_sensor()
            sensor_gaze = status.direct_gaze_sensor()
            sensor_audio = status.direct_audio_sensor()

            if not all(s.connected for s in [sensor_world, sensor_gaze, sensor_audio]):
                logging.error("Not all required sensors are connected. Aborting.")
                return

            logging.info("All sensors connected.")
            restart_on_disconnect = True

            # Initialize Queues
            queue_video = asyncio.Queue()
            queue_gaze = asyncio.Queue()
            queue_audio = asyncio.Queue()
            audio_playback_queue = Queue()  # For communication with the audio thread

            # Create tasks for receiving and processing data
            tasks = []
            audio_playback_thread = None
            try:
                # Sensor data enqueuing tasks
                tasks.extend((
                    asyncio.create_task(
                        enqueue_sensor_data(
                            receive_video_frames(
                                sensor_world.url, run_loop=restart_on_disconnect
                            ),
                            queue_video,
                        )
                    ),
                    asyncio.create_task(
                        enqueue_sensor_data(
                            receive_gaze_data(
                                sensor_gaze.url, run_loop=restart_on_disconnect
                            ),
                            queue_gaze,
                        )
                    ),
                    asyncio.create_task(
                        enqueue_sensor_data(
                            receive_audio_frames(
                                sensor_audio.url, run_loop=restart_on_disconnect
                            ),
                            queue_audio,
                        )
                    ),
                ))

                # Audio management task
                audio_manager_task = asyncio.create_task(
                    manage_audio_playback(queue_audio, audio_playback_queue)
                )
                tasks.append(audio_manager_task)

                # Run the main drawing loop
                await match_and_draw(queue_video, queue_gaze)

            finally:
                logging.info("Shutting down...")
                stop_audio_event.set()
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)

                # Find the audio thread to join it
                for thread in threading.enumerate():
                    if thread.name == "AudioPlaybackThread":
                        audio_playback_thread = thread
                        break

                if audio_playback_thread and audio_playback_thread.is_alive():
                    # Put a final None to ensure the audio thread's queue.get() unblocks
                    audio_playback_queue.put(None)
                    audio_playback_thread.join(timeout=2)
                    if audio_playback_thread.is_alive():
                        logging.warning("Audio thread did not terminate cleanly.")
                cv2.destroyAllWindows()
                logging.info("Cleanup complete.")


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
