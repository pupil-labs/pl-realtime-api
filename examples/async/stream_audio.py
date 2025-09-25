import asyncio
import contextlib
import logging

from pupil_labs.realtime_api import (
    Device,
    Network,
    receive_audio_frames,
)

logging.basicConfig(level=logging.INFO)


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
                async for audio_frame in audio_generator:
                    print(audio_frame)

    except asyncio.CancelledError:
        logging.info("Main task cancelled.")
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received, initiating shutdown.")
    finally:
        logging.info("Cleaning up resources...")


if __name__ == "__main__":
    # Use contextlib.suppress to avoid a traceback on KeyboardInterrupt
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
