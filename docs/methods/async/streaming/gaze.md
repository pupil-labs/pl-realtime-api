# Streaming Gaze Data

Use [`receive_gaze_data`][pupil_labs.realtime_api.streaming.receive_gaze_data] to subscribe to gaze data.

This function can return different types of gaze data ([GazeDataType][pupil_labs.realtime_api.streaming.gaze.GazeDataType]) depending on the device and its configuration:

-   [GazeData][pupil_labs.realtime_api.streaming.gaze.GazeData] object for Pupil Invisible or Neon without "Compute eye state" enabled.
-   [EyestateGazeData][pupil_labs.realtime_api.streaming.gaze.EyestateGazeData] or [EyestateEyelidGazeData][pupil_labs.realtime_api.streaming.gaze.EyestateEyelidGazeData] for Neon with "Compute eye state" enabled, depending on the version of the Neon Companion app.
-   Starting from Neon Companion app version +2.9.31, both binocular and monocular gaze data are exposed, it can return [BinoAndDualMonoGazeData][pupil_labs.realtime_api.streaming.gaze.BinoAndDualMonoGazeData] or [EyestateEyelidDualMonoGazeData][pupil_labs.realtime_api.streaming.gaze.EyestateEyelidDualMonoGazeData].

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

=== "Gaze data (Dual Mono)"

     <!-- badge:product Neon -->
     <!-- badge:companion +2.9.31 -->
     <!-- badge:version +1.8.0 -->

    ```py linenums="0"
    BinoAndDualMonoGazeData(
    	x=848.9487915039062,
    	y=474.46356201171875,
    	worn=True,
    	mono_left_x=895.11083984375,
    	mono_left_y=477.2065734863281,
    	mono_right_x=800.8253173828125,
    	mono_right_y=469.348388671875,
    	timestamp_unix_seconds=1772109976.1031907
    )
    ```

    This method exposes gaze data for Neon in Dual Mono mode, which includes binocular and monocular gaze data.
    ??? quote "BinoAndDualMonoGazeData"

    	::: pupil_labs.realtime_api.streaming.gaze.BinoAndDualMonoGazeData

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

=== "Dual Mono and Eye State & Eye Lid"

    <!-- badge:product Neon -->
    <!-- badge:companion +2.9.31 -->
    <!-- badge:version +1.8.0 -->

    ```py linenums="0"
    EyestateEyelidDualMonoGazeData(
    	x=852.3287353515625,
    	y=517.3056030273438,
    	worn=False,
    	pupil_diameter_left=4.567640781402588,
    	eyeball_center_left_x=-32.25,
    	eyeball_center_left_y=18.6875,
    	eyeball_center_left_z=-44.9375,
    	optical_axis_left_x=0.20407231152057648,
    	optical_axis_left_y=-0.020999005064368248,
    	optical_axis_left_z=0.9787306189537048,
    	pupil_diameter_right=3.035294771194458,
    	eyeball_center_right_x=30.15625,
    	eyeball_center_right_y=14.375,
    	eyeball_center_right_z=-43.3125,
    	optical_axis_right_x=-0.08533422648906708,
    	optical_axis_right_y=-0.019046271219849586,
    	optical_axis_right_z=0.9961703419685364,
    	eyelid_angle_top_left=-0.63037109375,
    	eyelid_angle_bottom_left=-1.138671875,
    	eyelid_aperture_left=6.09653902053833,
    	eyelid_angle_top_right=-0.06329345703125,
    	eyelid_angle_bottom_right=0.1409912109375,
    	eyelid_aperture_right=2.228158473968506,
    	gaze_mono_left_x=864.9857177734375,
    	gaze_mono_left_y=526.5974731445312,
    	gaze_mono_right_x=834.6492309570312,
    	gaze_mono_right_y=481.4454040527344,
    	timestamp_unix_seconds=1772108289.6118817
    )
    ```
     This method exposes binocular and monocular gaze data, [pupil diameter](https://docs.pupil-labs.com/neon/data-collection/data-streams/#pupil-diameters), and [eye poses](https://docs.pupil-labs.com/neon/data-collection/data-streams/#_3d-eye-poses).

    ??? quote "EyestateEyelidDualMonoGazeData"

    	::: pupil_labs.realtime_api.streaming.gaze.EyestateEyelidDualMonoGazeData

You can learn more about the payload in the [Under the Hood](../../../guides/under-the-hood.md) guide.

## Full Code Examples

??? example "Check the whole example code here"

    ```py title="stream_gaze.py" linenums="1"
    --8<-- "examples/async/stream_gaze.py"
    ```
