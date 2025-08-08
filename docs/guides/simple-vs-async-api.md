# Simple vs. Async API

The module provides two conceptionally different APIs:

1. The [`async`](../api/async.md) interface is using Python's [asyncio](https://docs.python.org/3/library/asyncio.html) in order to implement non-blocking asynchronous communication. It provides composable components for each feature of the Network API. This means that you need to select and combine the functionality for your own needs, e.g. [stream_video_with_overlayed_gaze](../../methods/async/streaming/scene-camera/#scene-camera-video-with-overlayed-gaze) example. The `async` functionality is implemented in the top-level [`pupil_labs.realtime_api`][pupil_labs.realtime_api] namespace.

2. The [`simple`][pupil_labs.realtime_api.simple] interface wraps around the `async` one, sacrificing flexibility for the sake of ease of use. It tries to anticipate and provide a solution for the most common use cases. Note, all `simple` API functionality can be found in the [`pupil_labs.realtime_api.simple`][pupil_labs.realtime_api.simple] namespace.

!!! danger "Do not mix async and simple components!"

      The `async` and `simple` components are not compatible with each other! Do not mix
      them!

## Device Classes

There are three different `Device` classes that one needs to differentiate:

1. [`pupil_labs.realtime_api.simple.device.Device`][pupil_labs.realtime_api.simple.device.Device]
   Easy-to-use class that auto-connects to the Companion device on `__init__` to request the [current status](../../methods/simple/connect-to-a-device/#device-information-automatic-status-updates) and to keep it up-to-date via the [Websocket API](../../methods/simple/connect-to-a-device/#continuously-monitor-status-updates). The phone's state is mirrored and cached in the corresponding attributes. Accessing the attributes is instant and does not need to perform a request to the phone. The class initiates streaming on demand ([pupil_labs.realtime_api.simple.Device.streaming_start][]) or when needed (any of the `simple.Device.receive_*`methods being called). Can be initialised with an explicit IP address and port number. Also, returned by the`pupil_labs.realtime_api.simple.discover_*` functions.

2. [`pupil_labs.realtime_api.models.DiscoveredDeviceInfo`][pupil_labs.realtime_api.models.DiscoveredDeviceInfo]
   Meta-information about discovered devices, e.g. IP address, port number, etc. Not
   able to initiate any connections on its own. Used to configure the following class:

3. [`pupil_labs.realtime_api.device.Device`][pupil_labs.realtime_api.device.Device]
   Does not connect to the Companion device on `__init__` - only explicitly on calls like [pupil_labs.realtime_api.device.Device.get_status][]. Subscription to the [`Websocket API`][pupil_labs.realtime_api.device.StatusUpdateNotifier], [streaming](../api/async.md#streaming), and [`clock offset estimation`](../api/async.md#pupil_labs.realtime_api.time_echo) are implemented in separate components.

## When to use which API?

The `simple` API is the best choice for most users. It is easy to use and provides a high-level interface for common tasks. The `async` API is more flexible and powerful, but it requires a deeper understanding of asynchronous programming and the underlying components. If you need to implement custom functionality or have specific performance requirements, the `async` API may be the better choice.
