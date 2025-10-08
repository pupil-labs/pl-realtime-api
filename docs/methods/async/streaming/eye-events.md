# Blinks, fixations & saccades

<!-- badge:product Neon -->
<!-- badge:companion +2.9.0 -->
<!-- badge:version +1.5.0 -->

Using the [`receive_eye_events_data`][pupil_labs.realtime_api.streaming.receive_eye_events_data] method, you can receive eye events such as blinks, saccades or fixations. The data returned is either an instance of:

!!! warning

    Requires the "Compute fixations" setting to be enabled in the Companion Device.

### [`FixationEventData`][pupil_labs.realtime_api.streaming.eye_events.FixationEventData]

Defines a full [fixation or saccade](https://docs.pupil-labs.com/neon/data-collection/data-streams/#fixations-saccades) event. They would look as follow, with event_type being either `0` for saccades or `1` for fixations.

=== "Saccade"

    ```py linenums="0"
    FixationEventData(
    	event_type=0,
    	start_time_ns=1744625900502677306,
    	end_time_ns=1744625900562676306,
    	start_gaze_x=768.2272338867188,
    	start_gaze_y=685.6964721679688,
    	end_gaze_x=716.1095581054688,
    	end_gaze_y=493.5322570800781,
    	mean_gaze_x=747.7811279296875,
    	mean_gaze_y=597.7672119140625,
    	amplitude_pixels=199.10633850097656,
    	amplitude_angle_deg=12.716423988342285,
    	mean_velocity=3318.313232421875,
    	max_velocity=7444.6396484375,
    	rtp_ts_unix_seconds=1744626471.955861
    )
    ```

=== "Fixation"

    ```py linenums="0"
    FixationEventData(
    	event_type=1,
    	start_time_ns=1744625967695094306,
    	end_time_ns=1744625968135465306,
    	start_gaze_x=870.0199584960938,
    	start_gaze_y=311.0625,
    	end_gaze_x=730.7664794921875,
    	end_gaze_y=264.4870300292969,
    	mean_gaze_x=839.43115234375,
    	mean_gaze_y=280.5098876953125,
    	amplitude_pixels=146.83596801757812,
    	amplitude_angle_deg=9.18490982055664,
    	mean_velocity=272.82110595703125,
    	max_velocity=1415.25048828125,
    	rtp_ts_unix_seconds=1744626539.528702
    )
    ```

??? quote "FixationEventData"

    ::: pupil_labs.realtime_api.streaming.eye_events.FixationEventData

### [`FixationOnsetEventData`][pupil_labs.realtime_api.streaming.eye_events.FixationOnsetEventData]

This defines a [fixation or saccade](https://docs.pupil-labs.com/neon/data-collection/data-streams/#fixations-saccades) onset event, and they would look as follows:

=== "Saccade Onset"

    ```py linenums="0"
    FixationOnsetEventData(event_type=2, start_time_ns=1744626187872119306, rtp_ts_unix_seconds=1744626759.2655792)
    ```

=== "Fixation Onset"

    ```py linenums="0"
    FixationOnsetEventData(event_type=3, start_time_ns=1744626187872119306, rtp_ts_unix_seconds=1744626759.2655792)
    ```

??? quote "FixationOnsetEventData"

    ::: pupil_labs.realtime_api.streaming.eye_events.FixationOnsetEventData

### [`BlinkEventData`][pupil_labs.realtime_api.streaming.eye_events.BlinkEventData]

Finally, BlinkEventData determines a [blink](https://docs.pupil-labs.com/neon/data-collection/data-streams/#blinks) event.

```py linenums="0"
BlinkEventData(
	event_type=4,
	start_time_ns=1744626029708811306,
	end_time_ns=1744626029919061306,
	rtp_ts_unix_seconds=1744626601.1020627
)
```

??? quote "BlinkEventData"

    ::: pupil_labs.realtime_api.streaming.eye_events.BlinkEventData

## Example

If you ran the example you will get an output simmilar to this:

```py linenums="0"
[FIXATION] event with duration of 3.93 seconds.
[SACCADE] event with 43° amplitude.
[BLINK] blinked at 10:35:07 UTC
```

??? example "Check the whole example code here"

    ```py title="stream_eye_events" linenums="1"
    --8<-- "examples/async/stream_eye_events.py"
    ```
