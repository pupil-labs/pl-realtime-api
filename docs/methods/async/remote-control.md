With the device connected, you can remotely control your [device][pupil_labs.realtime_api.device.Device], similarly to the [Monitor App](https://docs.pupil-labs.com/neon/data-collection/monitor-app/) and start, stop, save and annotate recordings.

## Start a Recording

Use [`device.recording_start`][pupil_labs.realtime_api.device.Device.recording_start] to start a recording on the device and return the recording ID.

```py linenums="1" title="start_stop_recordings.py" hl_lines="5"
--8<-- "examples/async/start_stop_recordings.py:23:34"
```

```linenums="0"
Initiated recording with id 54e7d0bb-5b4c-40e6-baed-f2e11eb4f53b
```

With a recording ongoing, you can:

## Send event

Save [events](https://docs.pupil-labs.com/neon/data-collection/events/) using the [`device.send_event`][pupil_labs.realtime_api.Device.send_event] method. By default, the Neon device receiving the event will assign a timestamp to it, using the time of arrival. Optionally, you can set a custom nanosecond timestamp for your event instead.

=== "Timestamped on Arrival (Host/Companion Device)"

    ```py linenums="1" title="send_event.py"
    await device.send_event("test event")
    ```
    ```linenums="0"
    Event(name=test event recording_id=None timestamp_unix_ns=1744271292116000000 datetime=2025-04-10 09:48:12.116000)
    ```

=== "With Explicit Timestamp"

    ```py linenums="0" title="send_event.py"
     await device.send_event(
    	"test event", event_timestamp_unix_ns=time.time_ns()
    )
    ```
    ```linenums="0"
    Event(name=test event recording_id=None timestamp_unix_ns=1744271291692745000 datetime=2025-04-10 09:48:11.692745)
    ```

Events will **only** be saved if the recording is running. If you send an event while there is no recording, it will be discarded.

### Check for Errors

<!-- badge:product Neon -->
<!-- badge:companion +2.9.0 -->
<!-- badge:version +1.5.0 -->

Errors can happen, but now you can also monitor them remotely, by looking for stream_errors on the [`component`][pupil_labs.realtime_api.models.Component] while updating the status, you can get notified of WatchDog errors during your recording.

```py linenums="0" title="start_stop_recordings.py"
--8<-- "examples/async/start_stop_recordings.py:7:13"

			...

--8<-- "examples/async/start_stop_recordings.py:24:25"
```

```linenums="0"
Error: Recording Watchdog failure
```

## Stop & Save a Recording

Likewise you can stop and save a recording using [`device.recording_stop_and_save`][pupil_labs.realtime_api.device.Device.recording_stop_and_save]. Note that if you have a mandatory question that is not filled, the recording will not be saved until that question is answered.

```py linenums="0" title="start_stop_recordings.py"
await device.recording_stop_and_save()
```

```linenums="0"
Recording stopped and saved
```

## Cancel a Recording

You can also cancel([`device.recording_cancel`][pupil_labs.realtime_api.device.Device.recording_cancel]) a recording if you don't want to save it. This will delete the recording and all its data.

```py linenums="0" title="start_stop_recordings.py"
await device.recording_cancel()
```

## Full Code Examples

??? example "Check the whole example code here"

    ```py title="start_stop_recordings.py" linenums="1"
    --8<-- "examples/async/start_stop_recordings.py"
    ```

    ```py title="send_event.py" linenums="1"
    --8<-- "examples/async/send_event.py"
    ```
