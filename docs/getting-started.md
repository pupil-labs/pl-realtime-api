The Real-time Python Client comes in two flavours, [simple][pupil_labs.realtime_api.simple] and [async][pupil_labs.realtime_api]. For most applications the `simple` interface is appropriate and we recommend it for new users. The `async` interface uses Python's asyncio features to enable non-blocking communication, which can be beneficial for applications with very strict latency requirements. It is more difficult to use though and for most users the `simple` interface will suffice. To learn more, check out the [Simple vs Async guide](./guides/simple-vs-async-api.md).

In the examples below, we will use the `simple` interface. We are assuming a Neon device is used, but the same code works for Pupil Invisible devices analoguously as well.

## Installation

The package is available on PyPI and can be installed using pip:

```sh
pip install pupil-labs-realtime-api
```

!!! warning "Python Compatibility"

    This package requires Python **3.10** or higher. For compatibility with Python 3.9 you can consider user older versions of this package `<1.6`.

    ```python
    pip install pupil-labs-realtime-api<1.6
    ```

## Connecting to a Device & Receiving Data

Using the [`discover_one_device`][pupil_labs.realtime_api.simple.discover_one_device] function to connect to a Neon device in your local network. Make sure the Neon Companion app is running! If no device can be found, please check the [troubleshooting section](./troubleshooting.md).

Using the [`receive_matched_scene_video_frame_and_gaze`][pupil_labs.realtime_api.simple.Device.receive_matched_scene_video_frame_and_gaze] method, you can receive the current scene camera frame and gaze sample. This method ensures that both samples are matched temporally.

The following example uses these methods to visualize a real-time gaze overlay on the scene camera frame:

```py
from pupil_labs.realtime_api.simple import discover_one_device
import cv2

device = discover_one_device()
print(f"Successfully connected to device with serial {device.serial_number_glasses}")

while True:
    frame, gaze = device.receive_matched_scene_video_frame_and_gaze()
    cv2.circle(
        frame.bgr_pixels,
        (int(gaze.x), int(gaze.y)),
        radius=80,
        color=(0, 0, 255),
        thickness=15,
    )

    cv2.imshow("Scene camera with gaze overlay", frame.bgr_pixels)
    if cv2.waitKey(1) & 0xFF == 27:
        break
```

## More Data & Remote Control

Many more data streams are available in real-time, including fixations, blinks, pupil diameter, IMU data and more. You can also control the device remotely, for example to start or stop a recording. Lastly, you can also save events as part of running recordings, to automatically annotate your data via the API.

All of these features are demonstrated and explained in more detail in the [Simple API](./methods/simple.md) section. More involved example applications can be found in the [Cookbook](./cookbook/index.md). All methods are documented in the [API reference and Code Examples](./methods/index.md).
