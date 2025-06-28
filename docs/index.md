---
hide:
    - feedback
---

--8<-- "README.md:0:9"

This is the documentation for the Pupil Labs Real-Time Python client, which allows you to stream data from Neon and Pupil Invisible devices in real time, as well as remote control them.

Head to the [Getting Started](./getting-started.md) section to start learning how to use this client!

Real-time access to eye tracking data and control over the generating devices is critical for many applications, from gaze-driven interaction tools to tightly timed experiments. Neon and Pupil Invisible devices enable such applications via their [Real-Time Network API](https://github.com/pupil-labs/realtime-network-api).

The Pupil Labs Real-Time Python client provides a high-level and very easy-to-use interface to this API, allowing developers and researchers to quickly build applications.

Check out the [Cookbook](./cookbook/index.md) section for a list of example applications that use this library.

!!! question "_Not a programmer?_"

    If writing code isn’t your thing and you simply need a tool to monitor and control all your devices in real time, check out [Neon Monitor](https://docs.pupil-labs.com/neon/data-collection/monitor-app/).

!!! question "_Not a Python user?_"

    We offer a [Matlab wrapper](https://github.com/pupil-labs/pl-neon-matlab), a [C++ Client](https://github.com/pupil-labs/pl-realtime-cpp-client), and a [Unity3D (C#)](https://docs.pupil-labs.com/neon/neon-xr/neon-xr-core-package/) client. To implement your own client, please refer to [Under the Hood](./guides/under-the-hood.md).

!!! warning "_Using Pupil Core?_"

    This package is designed for use with Pupil Invisible and Neon.
    For Pupil Core, please check out the [Pupil Core Network API](https://docs.pupil-labs.com/core/developer/network-api/).
