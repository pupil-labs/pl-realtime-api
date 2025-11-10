# Streaming Gaze Data

Use [`receive_gaze_data`][pupil_labs.realtime_api.streaming.receive_gaze_data] to subscribe to gaze data.

This function can return different types of gaze data ([GazeDataType][pupil_labs.realtime_api.streaming.gaze.GazeDataType]) depending on the device and its configuration:

- [GazeData][pupil_labs.realtime_api.streaming.gaze.GazeData] object for Pupil Invisible or Neon without "Compute eye state" enabled.
- [EyestateGazeData][pupil_labs.realtime_api.streaming.gaze.EyestateGazeData] or [EyestateEyelidGazeData][pupil_labs.realtime_api.streaming.gaze.EyestateEyelidGazeData] for Neon with "Compute eye state" enabled, depending on the version of the Neon Companion app.

See below samples for each type of gaze data.

=== "Gaze data"

    ```py linenums="0"
    GazeData(
    	x=784.0623779296875,
    	y=537.4524536132812,
    	worn=False,
    	timestamp_unix_seconds=1744294828.3579288
    )
    ```

=== "With Eye State"

    <!-- badge:product Neon -->
    <!-- badge:companion +2.8.8 -->
    <!-- badge:version +1.2.0 -->

    ```py linenums="0"
    EyestateGazeData(
    	x=784.0623779296875,
    	y=537.4524536132812,
    	worn=False,
    	pupil_diameter_left=4.306737899780273,
    	eyeball_center_left_x=-29.3125,
    	eyeball_center_left_y=11.6875,
    	eyeball_center_left_z=-42.15625,
    	optical_axis_left_x=0.09871648252010345,
    	optical_axis_left_y=0.15512824058532715,
    	optical_axis_left_z=0.9829498529434204,
    	pupil_diameter_right=3.2171919345855713,
    	eyeball_center_right_x=33.21875,
    	eyeball_center_right_y=12.84375,
    	eyeball_center_right_z=-45.34375,
    	optical_axis_right_x=-0.20461124181747437,
    	optical_axis_right_y=0.1512681096792221,
    	optical_axis_right_z=0.9670844078063965,
    	timestamp_unix_seconds=1744294828.3579288
    )
    ```
     This method also provides [pupil diameter](https://docs.pupil-labs.com/neon/data-collection/data-streams/#pupil-diameters) and [eye poses](https://docs.pupil-labs.com/neon/data-collection/data-streams/#_3d-eye-poses).

=== "With Eye Lid data"

    <!-- badge:product Neon -->
    <!-- badge:companion +2.9.0 -->
    <!-- badge:version +1.3.6 -->

    ```py linenums="0"
    EyestateEyelidGazeData(
    	x=784.0623779296875,
    	y=537.4524536132812,
    	worn=False,
    	pupil_diameter_left=4.306737899780273,
    	eyeball_center_left_x=-29.3125,
    	eyeball_center_left_y=11.6875,
    	eyeball_center_left_z=-42.15625,
    	optical_axis_left_x=0.09871648252010345,
    	optical_axis_left_y=0.15512824058532715,
    	optical_axis_left_z=0.9829498529434204,
    	pupil_diameter_right=3.2171919345855713,
    	eyeball_center_right_x=33.21875,
    	eyeball_center_right_y=12.84375,
    	eyeball_center_right_z=-45.34375,
    	optical_axis_right_x=-0.20461124181747437,
    	optical_axis_right_y=0.1512681096792221,
    	optical_axis_right_z=0.9670844078063965,
    	eyelid_angle_top_left=-1.1484375,
    	eyelid_angle_bottom_left=-1.2763671875,
    	eyelid_aperture_left=1.6408717632293701,
    	eyelid_angle_top_right=-0.6259765625,
    	eyelid_angle_bottom_right=-1.2216796875,
    	eyelid_aperture_right=7.2039408683776855,
    	timestamp_unix_seconds=1744294828.3579288
    )
    ```
    This method also provides [eye openness](https://docs.pupil-labs.com/neon/data-collection/data-streams/#eye-openness) data.

You can learn more about the payload in the [Under the Hood](../../../guides/under-the-hood.md) guide.

## Full Code Examples

??? example "Check the whole example code here"

    ```py title="stream_gaze.py" linenums="1"
    --8<-- "examples/async/stream_gaze.py"
    ```
