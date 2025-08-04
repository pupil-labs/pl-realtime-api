# Connect to a Device

One of the first steps you need to carry to leverage the API is to connect to one device. This library offers you ways to find one or multiple devices connected to your local network. See below the different ways to connect to a device:

=== "Discover Devices"

    Using the [`discover_devices`][pupil_labs.realtime_api.discovery.discover_devices]:

    ```py title="discover_devices.py" linenums="1" hl_lines="10 15"
    --8<-- "examples/async/discover_devices.py"
    ```

=== "Connect Directly via IP Address"

    ```py linenums="0" hl_lines="4-5"
    from pupil_labs.realtime_api.device import Device

    # This address is just an example. Find out the actual IP address of your device!
    ip = "192.168.1.169"
    device = Device(address=ip, port="8080")
    ```

Make sure the Companion App is running! If no device can be found, please have a look at the [troubleshooting section](../../troubleshooting.md).

Below you can find a link to the full code example and the API referece for the returned Device object.

## Device Information & Automatic Status Updates

Once connected, the [`Device`][pupil_labs.realtime_api.device.Device] object, alows you to retrieve [`Status`][pupil_labs.realtime_api.models.Status] updates by calling [`get_status`][pupil_labs.realtime_api.device.Device.get_status].

This [`Status`][pupil_labs.realtime_api.models.Status] represents the full Companion's Device state, including sub-classes representing:

- [Phone][pupil_labs.realtime_api.models.Phone]

- [Hardware][pupil_labs.realtime_api.models.Hardware]

- [Sensors][pupil_labs.realtime_api.models.Sensor]

- [Recording][pupil_labs.realtime_api.models.Recording]

=== "Get Current Status"

    ```py title="get_status.py" linenums="0" hl_lines="2"
    --8<-- "examples/async/device_status_get_current.py:13:26"
    ```
    ```py linenums="0"
    Device IP address: 192.168.1.60
    Battery level: 78 %
    Connected glasses: SN -1
    Connected scene camera: SN -1
    World sensor: connected=True url=rtsp://192.168.1.60:8086/?camera=world&audioenable=on
    Gaze sensor: connected=True url=rtsp://192.168.1.60:8086/?camera=gaze&audioenable=on
    ```

=== "Update via Callback"

    ```py linenums="0" hl_lines="5"
    --8<-- "examples/async/device_status_update_via_callback.py:17:25"
    ```
    ```py linenums="0"
    Starting auto-update for 20 seconds
    Phone(battery_level=77, battery_state='OK', device_id='d55a33b5ab845785', device_name='Neon Companion', ip='192.168.1.60', memory=99877777408, memory_state='OK', time_echo_port=12321)
    Hardware(version='2.0', glasses_serial='-1', world_camera_serial='-1', module_serial='841684')
    Sensor(sensor='imu', conn_type='WEBSOCKET', connected=True, ip='192.168.1.60', params='camera=imu&audioenable=off', port=8686, protocol='rtsp', stream_error=False)
    Sensor(sensor='imu', conn_type='DIRECT', connected=True, ip='192.168.1.60', params='camera=imu&audioenable=on', port=8086, protocol='rtsp', stream_error=False)
    Sensor(sensor='world', conn_type='WEBSOCKET', connected=True, ip='192.168.1.60', params='camera=world&audioenable=off', port=8686, protocol='rtsp', stream_error=False)
    ```

Refer to the [Device API documentation](::: pupil_labs.realtime_api.device.Device) for more details.

??? quote "Device"

    ::: pupil_labs.realtime_api.device.Device

??? quote "DeviceBase"

    ::: pupil_labs.realtime_api.base.DeviceBase

??? quote "Status"

    ::: pupil_labs.realtime_api.models.Status

## Full Code Examples

??? example "Check the whole example code here"

    ```py title="discover_devices.py" linenums="1"
    --8<-- "examples/async/discover_devices.py"
    ```
    ```py title="device_status_get_current.py" linenums="1"
    --8<-- "examples/async/device_status_get_current.py"
    ```

    ```py title="device_status_update_via_callback.py" linenums="1"
    --8<-- "examples/async/device_status_update_via_callback.py"
    ```
