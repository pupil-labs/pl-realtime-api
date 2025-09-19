import asyncio
import contextlib
import logging
import typing as T

from pupil_labs.realtime_api import (
    AudioFrame,
    AudioPlayer,
    Device,
    Network,
    receive_audio_frames,
)

logging.basicConfig(level=logging.INFO)


async def enqueue_audio_data(
    audio_generator: T.AsyncIterator[AudioFrame],
    player: AudioPlayer,
) -> None:
    """Get audio frames from a generator, resample and put them into a queue."""
    logging.info("Audio enqueuer task started.")
    try:
        async for audio_frame in audio_generator:
            # We place the resampled ndarray (s16) in the queue
            # for the audio callback to consume.
            for resampled_chunk in audio_frame.to_resampled_ndarray():
                player.add_data(resampled_chunk.T)
    except asyncio.CancelledError:
        logging.info("Audio enqueuer task cancelled.")
    except Exception:
        logging.exception("An error occurred in the audio enqueuer task.")
    finally:
        logging.info("Audio enqueuer task finished. Signaling end of stream.")
        player.close()  # Signal the audio playback thread to stop


async def main():
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
                player = AudioPlayer(
                    samplerate=sample_rate,
                    channels=channels,
                    dtype="int16",
                )

                player.start()

                # Start the asyncio task to enqueue audio data from the generator
                enqueue_task = asyncio.create_task(
                    enqueue_audio_data(audio_generator, player)
                )

                # Prime the queue with the first frame we already extracted
                for resampled_chunk in first_frame.to_resampled_ndarray():
                    player.add_data(resampled_chunk.T)

                # Wait for the enqueuer task to complete or be cancelled
                await enqueue_task

    except asyncio.CancelledError:
        logging.info("Main task cancelled.")
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received, initiating shutdown.")
    finally:
        logging.info("Cleaning up resources...")
        player.close()

        logging.info("Cleanup complete.")


if __name__ == "__main__":
    # Use contextlib.suppress to avoid a traceback on KeyboardInterrupt
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
