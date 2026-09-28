# Stream Eye Cameras

<!-- badge:product Neon -->
<!-- badge:version +1.1.2 -->

Neon allows you to receive the eye cameras video stream with timestamps. Using the same [`receive_video_frames`][pupil_labs.realtime_api.streaming.receive_video_frames] method used for the scene camera, but using the `sensor.eyes` that you can withdraw from [direct_eyes_sensor][pupil_labs.realtime_api.models.Status.direct_eyes_sensor].

```py linenums="0"
status = await device.get_status()
sensor_eyes = status.direct_eyes_sensor()
async for frame in receive_video_frames(
    sensor_eyes.url, run_loop=restart_on_disconnect
):
    bgr_buffer = frame.bgr_buffer()
```

<figure markdown="span">
![Eye Cameras](../../../assets/eye_cameras.webp){ loading=lazy }
</figure>

??? quote "VideoFrame"

    ::: pupil_labs.realtime_api.streaming.video.VideoFrame

??? example "Check the whole example code here"

    ```py title="stream_eyes_camera_video.py" linenums="1"
    --8 < --"examples/async/stream_eyes_camera_video.py"
    ```
