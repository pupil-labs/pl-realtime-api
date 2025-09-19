from pupil_labs.realtime_api.simple import discover_one_device

# Look for devices. Returns as soon as it has found the first device.
print("Looking for the next best device...")
device = discover_one_device(max_search_duration_seconds=10)
if device is None:
    print("No device found.")
    raise SystemExit(-1)
print(f"Found device: {device}")
device.streaming_start("audio")  # optional, if not called, stream is started on-demand
try:
    while True:
        audio_frame = device.receive_audio_frame(timeout_seconds=5)
        if audio_frame:
            print(audio_frame)
except KeyboardInterrupt:
    pass
finally:
    print("Stopping...")
    # device.streaming_stop()  # optional, if not called, stream is stopped on close
    device.close()  # explicitly stop auto-update
