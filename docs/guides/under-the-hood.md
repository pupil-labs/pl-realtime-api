# Under The Hood

This guide explains how the Pupil Labs' Realtime API works on the wire and how this
client library abstracts away some of the complexities of the underlying protocols.

## HTTP REST API

The Neon / Pupil Invisible Companion app hosts an [HTTP REST API](https://restfulapi.net/)
that can be used to query the phone's current state, remote control it, and look up
information about available data streams.

By default, the API is hosted at `http://neon.local:8080/` / `http://pi.local:8080/`, but the app will fallback to a different DNS name and/or port if the default values are taken by another app already.

The current connection details can be looked up under the app's main menu → Streaming or taping on the Streaming icon on Neon. Alternatively, you can use [Service discovery in the local network](#service-discovery-in-the-local-network) to find available devices.

!!! note

    The device serves the built-in monitor web app at the document root `/`. The API is served under the `/api` path. You can find the full [OpenAPI 3](https://swagger.io/specification/) specification of the REST API [here](https://pupil-labs.github.io/realtime-network-api/).

### Start/stop/cancel recordings

By sending [HTTP POST](https://developer.mozilla.org/en-US/docs/Web/HTTP/examples/POST) requests to the `/api/recording:*` endpoints, you can start, stop, and cancel recordings.

- [`POST /api/recording:start`](https://pupil-labs.github.io/realtime-network-api/#/recording/post_recording_start) - Starts a recording if possible
- [`POST /api/recording:stop_and_save`](https://pupil-labs.github.io/realtime-network-api/#/recording/post_recording_stop_and_save) - Stops and saves the running recording if possible
- [`POST /api/recording:cancel`](https://pupil-labs.github.io/realtime-network-api/#/recording/post_recording_cancel) - Stops and discards the running recording if possible

!!! warning

    In specific situations, the app will not comply with the request to start a new
    recording:

    - the selected template has required fields
    - the available storage amount is too low
    - the device battery is too low
    - no wearer has been selected
    - no workspace has been selected
    - the setup bottom sheets have not been completed

!!! seealso

    **`Simple` blocking implementations**

    - [`pupil_labs.realtime_api.simple.Device.recording_start`][]
    - [`pupil_labs.realtime_api.simple.Device.recording_stop_and_save`][]
    - [`pupil_labs.realtime_api.simple.Device.recording_cancel`][]

    **Asynchronous implementations**

    - [`pupil_labs.realtime_api.device.Device.recording_start`][]
    - [`pupil_labs.realtime_api.device.Device.recording_stop_and_save`][]
    - [`pupil_labs.realtime_api.device.Device.recording_cancel`][]

### Send events

By [HTTP POSTing](https://developer.mozilla.org/en-US/docs/Web/HTTP/examples/POST) requests to the `/api/event` endpoint, you can send labeled events to the device. Events will be timestamped on reception. Alternatively, you can provide a Unix-epoch timestamp in nanosecond. This is recommended if you want to control the timing of the event.

- [`POST /api/event`](https://pupil-labs.github.io/realtime-network-api/#/events/post_event) - Sends an event to the device

!!! seealso
**Implementations**

    - `Simple` blocking: [`pupil_labs.realtime_api.simple.Device.send_event`][]
    - Asynchronous: [`pupil_labs.realtime_api.device.Device.send_event`][]

### Get Current Status

By sending a [HTTP GET](https://developer.mozilla.org/en-US/docs/Web/HTTP/examples/GET) request to the `/api/status` endpoint, you can receive information about the device's current status. This includes information about the battery and storage capacities, connected sensors, and running recordings.

- [`GET /api/status`](https://pupil-labs.github.io/realtime-network-api/#/status/get_status) - Receive status from device

!!! seealso

    Asynchronous implementations: [`pupil_labs.realtime_api.device.Device.get_status`][]

## Websocket API

In addition to the HTTP REST API above, the Neon / Pupil Invisible Companion device also pushes status updates via a [websocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) connection. It is hosted on the same port as the REST API. By default, you can connect to it via `ws://neon.local:8080/api/status` or `ws://pi.local:8080/api/status`.

!!! tip

    You can use this [website](http://livepersoninc.github.io/ws-test-page/) to test the websocket connection.

The messages published via this connection have the same format as the [Get Current Status](#get-current-status) endpoint.

## Streaming API

The Neon / Pupil Invisible Companion app uses the RTSP protocol ([RFC 2326](https://datatracker.ietf.org/doc/html/rfc2326)) to stream scene video and gaze data. Under the hood, communication is three-fold:

- [RTSP](#rtsp) (RealTime Streaming Protocol) - Provides meta data about the corresponding stream
- [RTP](#rtp) (Realtime Transport Protocol) - Data delivery channel, contains actual payloads
- [RTCP](#rtcp) (RTP Control Protocol) - Provides absolute time information to align multiple streams

The necessary connection information is made available via the [Sensor model](https://github.com/pupil-labs/realtime-network-api/blob/main/openapi_specification.yaml#L281) as part of the [Get Current Status](#get-current-status) and [Websocket API](#websocket-api).

The RTSP connection URL follows the following pattern:

```sh
rtsp://<ip>:<port>/?<params>
```

!!! info

    Each stream is available via two connection types:

    - `DIRECT` - direct RTSP connection, as described in this document
    - `WEBSOCKET` - tunneling RTSP over a websocket connection to make it
    available to web browsers

!!! seealso

    The Realtime Network API exposes this information via
    [`pupil_labs.realtime_api.models.Status.direct_world_sensor`][] and
    [`pupil_labs.realtime_api.models.Status.direct_gaze_sensor`][], returning
    [`pupil_labs.realtime_api.models.Sensor`][] instances.

### RTSP

!!! abstract

    The Real Time Streaming Protocol, or RTSP, is an application-level protocol for control over the delivery of data with real-time properties.

    Source: [https://datatracker.ietf.org/doc/html/rfc2326](https://datatracker.ietf.org/doc/html/rfc2326)

Of the various [methods](https://datatracker.ietf.org/doc/html/rfc2326#section-6.1) defined in the RTSP protocol, [SETUP](https://datatracker.ietf.org/doc/html/rfc2326#section-10.4) and [DESCRIBE](https://datatracker.ietf.org/doc/html/rfc2326#section-10.2) are particularly important for the transmission of the stream's meta and connection
information.

During the SETUP method, client and server exchange information about their corresponding port numbers for the [RTP](#rtp) and [RTCP](#rtcp) connections.

The DESCRIBE response contains [SDP](https://datatracker.ietf.org/doc/html/rfc2326#page-80)(Session Description Protocol) data, describing the following stream attributes (via the [media's rtpmap](https://datatracker.ietf.org/doc/html/rfc2326#appendix-C.1.3)):

- `encoding` - The encoding of the stream, e.g. `H264`
- `clockRate` - The clock rate of the stream's relative clock

For video, it also exposes the [sprop-parameter-sets](https://datatracker.ietf.org/doc/html/rfc6184#section-8.2.1) via its [format-specific parameters](https://datatracker.ietf.org/doc/html/rfc5576#section-6.3) (`fmtp`).
These contain crucial information in order to initialize the corresponding video decoder.

!!! danger

    Each stream has its own clock rate. For temporal alignment, the clock offset between
    the stream's relative clock and the absolute NTP clock has to be calculated. See
    [RTCP](#rtcp) below.

!!! seealso

    To encode gaze data, a custom encoding called `com.pupillabs.gaze1` is used.
    You can find more information about it below.

### RTP

!!! abstract

    [The real-time transport protocol] provides end-to-end network transport functions suitable for applications transmitting real-time data, such as audio, video or simulation data, over multicast or unicast network services. [...] The data transport is augmented by a control protocol ([RTCP](#rtcp)) [...]. [RTP](#rtp) and [RTCP](#rtcp) are	designed to be independent of the underlying transport and network layers.

    Source: [https://datatracker.ietf.org/doc/html/rfc3550](https://datatracker.ietf.org/doc/html/rfc3550)

Payloads can be split across multiple RTP packets. Their order can be identified via the packet header's [sequence number](https://datatracker.ietf.org/doc/html/rfc1889#section-5.1).
Packets belonging to the same payload have the same timestamp. The payloads can be decoded individually. See [Decoding Gaze Data](#decoding-gaze-data) and [Decoding Video Data](#decoding-video-data) below.

!!! seealso

    Read more about the RTP timestamp mechanism [here](https://datatracker.ietf.org/doc/html/rfc1889#section-5.1).

!!! seealso

    The Realtime Python API exposes raw RTP data via [`pupil_labs.realtime_api.streaming.base.RTSPRawStreamer.receive`][] and calculates relative RTP packet timestamps in [`pupil_labs.realtime_api.streaming.base._WallclockRTSPReader.relative_timestamp_from_packet`][].

### RTCP

The most important role that the RTP control protocol plays for the Pupil Labs Realtime Network API is to provide timestamps in relative stream time and in absolute NTP time ([SR RTCP Packet type](https://datatracker.ietf.org/doc/html/rfc1889#section-6.1)).

Relative timestamps are calculated by dividing the packet timestamp (numerator) by the clock rate (denominator), e.g. a timestamp of 250 at a clock rate of 50 Hz corresponds to `250 / 50 = 5` seconds.

!!! abstract

    Wallclock time (absolute date and time) is represented using the timestamp format of
    the [Network Time Protocol](https://datatracker.ietf.org/doc/html/rfc1305) (NTP),
    which is in seconds relative to 1 January **1900** 00:00:00 UTC. The full resolution
    NTP timestamp is a 64-bit unsigned fixed-point number with the integer part in the
    first 32 bits and the fractional part in the last 32 bits.

    Source: [https://datatracker.ietf.org/doc/html/rfc3550#section-4](https://datatracker.ietf.org/doc/html/rfc3550#section-4)

Knowing time points in both corresponding clocks, relative and absolute one, allows one
to calculate the clock offset between the two clocks. This is done by subtracting the
one from the other. The offset is then added to new relative timestamps to get the
corresponding time.

!!! danger

    The Realtime Python API converts absolute NTP timestamps to nanoseconds in **Unix**
    epoch (time since 1 January **1970** 00:00:00 UTC). This corresponds to the same
    time base and unit returned by `time.time_ns`.

### Decoding Gaze Data

Gaze data is encoded in network byte order (big-endian) and consists of:

1. `x` - Horizontal component of the gaze location in pixels within the scene camera's
   coordinate system. The value is encoded as a 32-bit float.
2. `y` - Vertical component of the gaze location in pixels within the scene camera's
   coordinate system. The value is encoded as a 32-bit float.
3. `worn` - Boolean indicating whether the user is wearing the device. The value is
   encoded as an unsigned 8-bit integer as either `255` (device is being worn) or `0` (device is _not_ being worn).

**Eye State Data (Optional)**

If eye state computation is enabled (not available for Pupil Invisible), additional parameters are included(all encoded as a 32-bit float):

4. **`pupil_diameter_left`**: Physical diameter of the left pupil in millimetres.
5. **`eyeball_center_left_x`**: X-coordinate of the left eyeball centre relative to the scene camera.
6. **`eyeball_center_left_y`**: Y-coordinate of the left eyeball centre relative to the scene camera.
7. **`eyeball_center_left_z`**: Z-coordinate of the left eyeball centre relative to the scene camera.
8. **`optical_axis_left_x`**: X-component of the left eye's optical axis vector.
9. **`optical_axis_left_y`**: Y-component of the left eye's optical axis vector.
10. **`optical_axis_left_z`**: Z-component of the left eye's optical axis vector.
11. **`pupil_diameter_right`**: Physical diameter of the right pupil in millimetres.
12. **`eyeball_center_right_x`**: X-coordinate of the right eyeball centre relative to the scene camera.
13. **`eyeball_center_right_y`**: Y-coordinate of the right eyeball centre relative to the scene camera.
14. **`eyeball_center_right_z`**: Z-coordinate of the right eyeball centre relative to the scene camera.
15. **`optical_axis_right_x`**: X-component of the right eye's optical axis vector.
16. **`optical_axis_right_y`**: Y-component of the right eye's optical axis vector.
17. **`optical_axis_right_z`**: Z-component of the right eye's optical axis vector.
18. **`timestamp_unix_seconds`**: Unix timestamp representing the time of data capture.

Each RTP packet contains one gaze datum. The payload length varies:

- **21 bytes**: When only gaze data is included. To unpack - (!ffB)
- **77 bytes**: When both gaze and eye state data are included. To unpack - (!ffBffffffffffffff)

!!! tip

    RTSP packets can be captured and analysed using **Wireshark**, a comprehensive network protocol analyser.
    This tool allows detailed inspection of packet data for in-depth analysis and troubleshooting.

!!! seealso

    The Realtime Python API exposes gaze data via
    [`pupil_labs.realtime_api.streaming.gaze.RTSPGazeStreamer.receive`][] and
    [`pupil_labs.realtime_api.streaming.gaze`][].

### Decoding Video Data

Video frames are split across multiple RTP packets. The payload is wrapped in the additional [Network Abstraction Layer](https://datatracker.ietf.org/doc/html/rfc6184#section-5.3) (NAL). This allows finding frame boundaries across fragmented payloads without relying on the RTP meta information.

Once the data is unpacked from the NAL, it can be passed to a corresponding video decoder, e.g. `pyav's av.CodecContext`.

!!! important

    The video decoder needs to be initialized with the [sprop-parameter-sets](https://datatracker.ietf.org/doc/html/rfc6184#section-8.2.1) exposed via the [RTSP](#rtsp) DESCRIBE method.

!!! seealso

    The Realtime Python API implements the NAL unpacking here:
    [`pupil_labs.realtime_api.streaming.nal_unit.extract_payload_from_nal_unit`][]

## Service discovery in the local network

To avoid having to manually copy the IP address from the Neon / Pupil Invisible Companion user interface, the application announces its REST API endpoint via [multicast DNS service discovery](https://en.wikipedia.org/wiki/Zero-configuration_networking#DNS-SD_with_multicast).
Specifically, it announces a service of type `_http._tcp.local.` and uses the following naming pattern:

```
PI monitor:<phone name>:<phone hardware id>._http._tcp.local.
```

!!! seealso

    The service name is exposed via
    - [`pupil_labs.realtime_api.models.DiscoveredDeviceInfo.name`][] and
    - [`pupil_labs.realtime_api.base.DeviceBase.full_name`[]].

    The phone name component is exposed via
    - [`pupil_labs.realtime_api.models.Phone.device_name`][] and
    - [`pupil_labs.realtime_api.simple.Device.phone_name`][].

    The phone hardware id component is exposed via
    - [`pupil_labs.realtime_api.models.Phone.device_id`][] and
    - [`pupil_labs.realtime_api.simple.Device.phone_id`][].

The client's [`pupil_labs.realtime_api.discovery`][] module uses the [`zeroconf`](https://python-zeroconf.readthedocs.io/en/stable/api.html#module-zeroconf) Python package under the hood to discover services.
