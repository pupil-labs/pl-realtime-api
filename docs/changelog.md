## 1.5.0

- Auto-start only necessary streams in Simple API
- Adds error information

## 1.4.0

- Adds eye events (blinks, fixations)

## 1.3.6

- Adds eyelid data

## 1.3.5

- Fixes streaming bug when audio is enabled

## 1.3.4

- Add av/cv issue workaround to example scripts

## 1.3.3

- Use pl-neon-recording for loading calibration data

## 1.3.0

- Add support for templates for Neon Companion app (2.8.25+)
    - Simple API
        - [pupil_labs.realtime_api.simple.Device.get_template][]
        - [pupil_labs.realtime_api.simple.Device.get_template_data][]
        - [pupil_labs.realtime_api.simple.Device.post_template_data][]
    - Async API
        - [pupil_labs.realtime_api.device.Device.get_template][]
        - [pupil_labs.realtime_api.device.Device.get_template_data][]
        - [pupil_labs.realtime_api.device.Device.post_template_data][]
- Add [simple_template_example][] example
- Add [async_template_example][] example

## 1.2.1

- Add typing annotations for various gaze data types

## 1.2.0

- Add support for streaming eye state data from Neon Companion app (2.8.8+)
    - [pupil_labs.realtime_api.streaming.gaze.EyestateGazeData][]

## 1.1.2

- Add support for streaming eyes video from Neon Companion app
    - Simple API
        - [pupil_labs.realtime_api.simple.Device.receive_eyes_video_frame][]
        - [pupil_labs.realtime_api.simple.Device.receive_matched_scene_and_eyes_video_frames_and_gaze][]
    - Async API
        - [pupil_labs.realtime_api.models.Status.direct_eyes_sensor][], providing an
          url that can be used with [pupil_labs.realtime_api.streaming.video.receive_video_frames][]
- Add async support for streaming IMU from Neon Companion app
    - Async API
        - [pupil_labs.realtime_api.streaming.imu.receive_imu_data][]

### 1.1.1

- Use `numpy.typing` instead of `nptyping`
- Add [simple_vs_async_api_guide][] guide

### 1.1.0

- Rename `pupil_labs.realtime_api.clock_echo` to [pupil_labs.realtime_api.time_echo][]
  and all corresponding class and function prefixes.
- Expose Time Echo port via [pupil_labs.realtime_api.models.Phone.time_echo_port][]
- Add simple API to estimate time offset [pupil_labs.realtime_api.simple.Device.estimate_time_offset][]
- Add simple and async time offset estimation examples

#### 1.1.0a2

- Internal feature

#### 1.1.0a1

- Add `pupil_labs.realtime_api.clock_echo`

### 1.0.1

- Require `nptyping<2.0.0` to avoid backwards incompatibility
- Update link to documentation in README

## 1.0.0.post1

- Improve front-page documentation

### 1.0.0

- Fixed wrong variable name and added default value - #11

## v1.0.0rc4

- Fix examples and documentation
- Finalize first draft of the [under_the_hood_guide][] guide

## v1.0.0rc3

- Fix documentation
- Revert: Remove [pupil_labs.realtime_api.simple.discover_one_device][]
- Revert: Add `pupil_labs.realtime_api.simple.Network`

## v1.0.0rc2

- Apply pre-commit fixes

## v1.0.0rc1

- Split [pupil_labs.realtime_api.simple][] into multiple files
- Remove `pupil_labs.realtime_api.discovery.discover_one_device`
- Remove `pupil_labs.realtime_api.simple.discover_one_device`
- Add `pupil_labs.realtime_api.simple.Network`
- Add [pupil_labs.realtime_api.discovery.Network][]

## v0.0.12

- Add [pupil_labs.realtime_api.models.UnknownComponentError][] and let
  [pupil_labs.realtime_api.models.parse_component][] raise it when a component
  could not be parsed/mapped
- Drop unknown components in [pupil_labs.realtime_api.models.Status.from_dict][]
  and [pupil_labs.realtime_api.device.Device.status_updates][], and warn about it

## v0.0.11

- Add [pupil_labs.realtime_api.models.NetworkDevice][]
- Create a new HTTP client session if necessary on [pupil_labs.realtime_api.device.Device.__aenter__][] method

## v0.0.10

- Remove `pupil_labs.realtime_api.simple.Device.recording_recent_action` and `pupil_labs.realtime_api.simple.Device.recording_duration_seconds`
- Fix Python 3.7 incompatiblity due to using the `name` argument in [asyncio.create_task][] (added in Python 3.8)

## v0.0.9

- Fix Python 3.7 compatibility
- Add `pupil_labs.realtime_api.discovery.discover_one_device`

## v0.0.8

- Rename `pupil_labs.realtime_api.basic` to [pupil_labs.realtime_api.simple][]
- Rename `pupil_labs.realtime_api.basic.Device.read_*()` methods to `Device.receive_*()`
- Rename `pupil_labs.realtime_api.simple.discovered_devices` to [pupil_labs.realtime_api.simple.discover_devices][]
- Add [pupil_labs.realtime_api.device.Device.status_updates()][] generator
- Move status update callback functionality into [pupil_labs.realtime_api.device.StatusUpdateNotifier][]
- Add [simple_auto_update_example][] example
- Add `pupil_labs.realtime_api.simple.Device.recording_recent_action` and `pupil_labs.realtime_api.simple.Device.recording_duration_seconds`
- Add streaming control functionality to [pupil_labs.realtime_api.simple.Device][]
    - [pupil_labs.realtime_api.simple.Device.streaming_start][]
    - [pupil_labs.realtime_api.simple.Device.streaming_stop][]
    - [pupil_labs.realtime_api.simple.Device.is_currently_streaming][]
- Fix examples

## v0.0.7

- Fix Python 3.7 and 3.8 compatibility

## v0.0.6

- Add [pupil_labs.realtime_api.simple.Device.receive_matched_scene_video_frame_and_gaze][]
- Add simple [stream_video_with_overlayed_gaze_example_simple][] example

## v0.0.5

- Add guides to documentation
- Add [stream_video_with_overlayed_gaze_example][] example
- Add [pupil_labs.realtime_api.simple][] API. See the [simple_examples][].
- Rename `pupil_labs.realtime_api.control` to [pupil_labs.realtime_api.device][].
- Rename `pupil_labs.realtime_api.base.ControlBase` to [pupil_labs.realtime_api.base.DeviceBase][].
- Rename `pupil_labs.realtime_api.simple.Control` to [pupil_labs.realtime_api.simple.Device][].
- Rename `pupil_labs.realtime_api.control.Control` to [pupil_labs.realtime_api.device.Device][].
- Rename `pupil_labs.realtime_api.models.DiscoveredDevice` to [pupil_labs.realtime_api.models.DiscoveredDeviceInfo][].
- Add sensor property accessors to [pupil_labs.realtime_api.simple.Device][].
- Add simple streaming with [pupil_labs.realtime_api.simple.Device.receive_scene_video_frame][]
  and [pupil_labs.realtime_api.simple.Device.receive_gaze_datum][].

## v0.0.4

- Include examples in documentation
- Implement [pupil_labs.realtime_api.models.Recording][] model class
- Add [pupil_labs.realtime_api.models.Status.recording][] attribute

## v0.0.3

- Move Control.Error to dedicated [pupil_labs.realtime_api.device.DeviceError][] class
- Implement [pupil_labs.realtime_api.streaming.gaze][] and
  [pupil_labs.realtime_api.streaming.video][] streaming

## v0.0.2

- Require [`aiohttp[speedups]`](https://docs.aiohttp.org/en/stable/)
- Implement [pupil_labs.realtime_api.discovery.discover_devices][]
- Implement [pupil_labs.realtime_api.device.Device][]
