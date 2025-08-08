# Connect to a Device

The first step when using the Real-time API is to connect your client to a Companion device, enabling communication between them.

The examples below demonstrate how to connect to one or more devices using our device discovery functions, as well as how
to connect directly via a device’s IP address.

Your device and the computer running the client must be connected to the same network, and the Companion app must be running.
If no device can be found, please refer to the [troubleshooting section](../../troubleshooting.md).

=== "Discover One Device"

    Using the [`discover_one_device()`][pupil_labs.realtime_api.simple.discover_one_device], you will get access to the first device it detects.

    ```py title="discover_devices.py" linenums="0" hl_lines="4"
    --8<-- "examples/simple/discover_devices.py:1:2,4:5"
    ```

=== "Discover Multiple Devices"

    Using the [`discover_devices()`][pupil_labs.realtime_api.simple.discover_devices], you can connect to more than one device.

    ```py title="discover_devices.py" linenums="0" hl_lines="4"
    --8<-- "examples/simple/discover_devices.py:1:2,8:9"
    ```

=== "Connect Directly via IP Address"

    There might be instances where devices can't be found due to the network, but you can always specify the IP address and port to simplify the process.

    ```py linenums="0" hl_lines="4-5"
    from pupil_labs.realtime_api.simple import Device

    # This address is just an example. Find out the actual IP address of your device!
    ip = "192.168.1.169"
    device = Device(address=ip, port="8080")
    ```

Make sure the Companion App is running! If no device can be found, please have a look at the [troubleshooting section](../../troubleshooting.md).

Below you can find a link to the full code example and the API referece for the returned Device object.

## Device Information & Automatic Status Updates

Once connected, the [`Device`][pupil_labs.realtime_api.simple.Device] object provides access to various properties of he Companion device and connected glasses, such as [battery level][pupil_labs.realtime_api.simple.Device.battery_level_percent],
[free storage][pupil_labs.realtime_api.simple.Device.memory_num_free_bytes],
and [serial numbers][pupil_labs.realtime_api.simple.Device.module_serial].

This class automatically monitors the Companion device in the background and mirrors its state accordingly.

=== "Get a snap of Status"

    ```python title="get_status.py" linenums="0"
    --8<-- "examples/simple/get_status.py"
    ```
    ```py title="Output" linenums="0"
    Phone IP address: 192.168.1.168
    Phone name: OnePlus8
    Battery level: 43%
    Free storage: 92.4 GB
    Serial number of connected glasses: h4gcf
    ```

=== "Continuously monitor Status Updates"

    ```python linenums="0"
    --8<-- "examples/simple/status_auto_update.py"
    ```

    ```title="Output" linenums="0"
    Looking for the next best device...
    Scene camera connected: True
    (Dis)connect the scene camera and hit enter...
    Scene camera connected: False
    ```

??? quote "Device Reference"

    ::: pupil_labs.realtime_api.simple.Device

## Full Code Examples

??? example "Check the whole example code here"

    ```py title="discover_devices.py" linenums="1"
    --8<-- "examples/simple/discover_devices.py"
    ```

    ```py title="get_status.py" linenums="1"
    --8<-- "examples/simple/get_status.py"
    ```

    ```python title="status_auto_update.py" linenums="0"
    --8<-- "examples/simple/status_auto_update.py"
    ```
