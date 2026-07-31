import asyncio
import logging

from rich import print  # noqa: A004

from pupil_labs.realtime_api import Device, DeviceError, Network, receive_video_frames


async def main():
    async with Network() as network:
        dev_info = await network.wait_for_new_device(timeout_seconds=5)

    if dev_info is None:
        print("No device could be found! Abort")
        return
    else:
        print(f"Connecting to {dev_info.addresses[0]}:{dev_info.port}")

    async with Device.from_discovered_device(dev_info) as device:
        # Initiate video stream before querying camera state to ensure camera is active
        # You could instead simply open the scene video preview in the companion app
        status = await device.get_status()
        sensor_world = status.direct_world_sensor()
        frames_itr = receive_video_frames(sensor_world.url)
        await anext(frames_itr)

        state = None
        try:
            state = await device.get_camera_state()
            print("Current state:", state)
        except DeviceError as err:
            print(err)
            print("Open the scene video preview in the companion app")

        try:
            await device.set_camera_state(
                ae_mode="auto",
                man_exp=50,
                gain=50,
                brightness=0,
                contrast=70,
                gamma=300,
                validate_with_state=state,
            )
        except DeviceError as err:
            print(err)

        await frames_itr.aclose()


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    asyncio.run(main())
