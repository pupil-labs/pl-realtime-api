## Time Offset Estimation

<!-- badge:version 1.1.0 -->

Additionally, we offer you a convenient function to estimate the time offset between the device and your computer using the [`TimeOffsetEstimator.estimate`][pupil_labs.realtime_api.time_echo.TimeOffsetEstimator.estimate] method.

See [`time_echo`][pupil_labs.realtime_api.time_echo] for details.

```py linenums="0"
--8<-- "examples/async/device_time_offset.py:27:29"
```

```py linenums="0"
Mean time offset: -37.53 ms
Mean roundtrip duration: 12.91 ms
```

??? example "Check the whole example code here"

    ```py title="device_time_offset.py" linenums="1"
    --8<-- "examples/async/device_time_offset.py"
    ```

!!! question "Wanna get super precise time sync?"

    Have a look at our tutorial [here](https://docs.pupil-labs.com/neon/data-collection/time-synchronization/).

## Camera calibration

<!-- badge:product Neon -->

Getting the camera calibration coefficients can be extremely useful for undistorting the video. You can receive camera calibration parameters using the [get_calibration][pupil_labs.realtime_api.device.Device.get_calibration] method.

```py linenums="0"
await device.get_calibration()
```

Returns a `pupil_labs.neon_recording.calib.Calibration` object.

```py linenums="0"
Calibration(
	version = np.uint8(1)
	serial = '841684'
	scene_camera_matrix = array([[896.23068471,   0.        , 790.8950718 ],
				[  0.        , 895.99428647, 593.30938736],
				[  0.        ,   0.        ,   1.        ]])
	scene_distortion_coefficients = array([-0.13185823,  0.11141446, -0.00072215, -0.00019211, -0.00102044,
				0.17091784,  0.05497444,  0.02371847])
	scene_extrinsics_affine_matrix = array([[1., 0., 0., 0.],
				[0., 1., 0., 0.],
				[0., 0., 1., 0.],
				[0., 0., 0., 1.]])
	right_camera_matrix = array([[140.03968681,   0.        ,  99.07925009],
				[  0.        , 140.16685902,  96.21073359],
				[  0.        ,   0.        ,   1.        ]])
	right_distortion_coefficients = array([ 4.88968666e-02, -1.28678179e-01, -2.42854366e-04,  6.16360859e-04,
				-6.13765032e-01, -4.34790467e-02,  3.41057533e-02, -6.83627299e-01])
	right_extrinsics_affine_matrix = array([[-0.8363896 ,  0.14588414,  0.52836567, 16.93598175],
				[ 0.05819079,  0.98211712, -0.17905241, 19.64488983],
				[-0.54503787, -0.11901156, -0.82992166, -7.03995514],
				[ 0.        ,  0.        ,  0.        ,  1.        ]])
	left_camera_matrix = array([[139.60850687,   0.        ,  93.21881139],
				[  0.        , 139.73659663,  95.43463863],
				[  0.        ,   0.        ,   1.        ]])
	left_distortion_coefficients = array([ 4.95496340e-02, -1.27421933e-01,  6.92379886e-04,  4.98479011e-04,
				-6.26153622e-01, -4.43117940e-02,  3.31060602e-02, -6.91888536e-01])
	left_extrinsics_affine_matrix = array([[ -0.83850485,  -0.13447338,  -0.52804023, -17.65301514],
				[ -0.05493483,   0.98499447,  -0.16360955,  19.88935852],
				[  0.54211783,  -0.10817961,  -0.83330995,  -7.48944855],
				[  0.        ,   0.        ,   0.        ,   1.        ]])
	crc = np.uint32(734156985)
)
```

!!! question "Wanna know how to undistort the video?"

    Get a look at [our tutorial](https://docs.pupil-labs.com/alpha-lab/undistort/).
