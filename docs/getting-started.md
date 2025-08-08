# Getting Started

Get the Real-time API running and stream data in two simple steps.

## 1. Install It

Open your terminal and use pip to install the package.

```sh
pip install pupil-labs-realtime-api
```

!!! warning "Python Compatibility"

    This package requires Python **3.10** or higher. For compatibility with Python 3.9 you can consider user older versions of this package `<1.6`.

    ```python
    pip install pupil-labs-realtime-api<1.6
    ```

## 2. Run the Script

Run the code below in your Python environment. Before you start, make sure the Neon Companion app is running and your
device is on the same network as your computer.

```python
from pupil_labs.realtime_api.simple import discover_one_device

try:
    # Look for a device on the network.
    print("Looking for a device...")
    device = discover_one_device(max_search_duration_seconds=10)
    if device is None:
        print("No device found.")
        raise SystemExit()

    print(f"Connected to {device.serial_number_glasses}. Press Ctrl-C to stop.")

    # Stream gaze data.
    while True:
        # receive_gaze_datum() will return the next available gaze datum
        # or block until one becomes available.
        gaze = device.receive_gaze_datum()
        # The gaze datum is a named tuple containing x, y, worn, and timestamp.
        # We can access these values as attributes.
        print(
            f"Timestamp: {gaze.timestamp_unix_seconds:.3f} | "
            f"Gaze (x,y): ({gaze.x:.2f}, {gaze.y:.2f}) | "
            f"Worn: {gaze.worn}"
        )

except KeyboardInterrupt:
    print("\nStopping...")
finally:
    # Cleanly close the connection
    if "device" in locals() and device:
        device.close()
    print("Connection closed.")
```

You will see a continuous stream of timestamps, gaze coordinates, and worn status printed to your console.

## How It Works

This script uses the [simple][pupil_labs.realtime_api.simple] interface, which is the easiest way to use the API
and is recommended for most applications.

-   `discover_one_device()`: Scans the local network and connects to the first available device.
-   `receive_gaze_datum()`: Fetches the next available gaze data point from the device.

## Simple vs. Async API

For more advanced use-cases, an [async](./api/async.md) interface is also available. This uses Python's asyncio
features to enable non-blocking communication, which can be beneficial for applications with strict latency requirements.
It is more difficult to use though and for most users the `simple` interface will suffice.

For a deeper dive, read the [Simple vs Async guide](./guides/simple-vs-async-api.md).

## Next Steps

You can stream much more than just gaze! For example, fixations, blinks, pupil data, and scene video with a live gaze
overlay. Remotely controlling recordings is also possible:

-   Explore more features and examples in the [Simple](./methods/simple.md) and [Async](./methods/async.md) methods sections.
-   Find advanced examples in the [Cookbook](./cookbook/index.md).
-   See all methods in the [API Reference](./modules.md).
