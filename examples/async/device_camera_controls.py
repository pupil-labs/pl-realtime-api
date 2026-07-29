import asyncio
import logging

from rich import print

from pupil_labs.realtime_api import Device, DeviceError, discover_devices


async def main():
    dev_info = None
    async for dev_info in discover_devices(timeout_seconds=10):
        if "9865e04c385bcb59" in dev_info.name:
            break

    if dev_info is None:
        print("No device could be found! Abort")
        return
    else:
        print(f"Connecting to {dev_info.addresses[0]}:{dev_info.port}")

    async with Device.from_discovered_device(dev_info) as device:
        state = None
        try:
            state = await device.get_camera_state()
            print("Current state:", state)
        except DeviceError as err:
            print(err)
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


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    asyncio.run(main())
