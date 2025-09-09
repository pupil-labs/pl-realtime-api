"""pupil_labs.realtime_api package.

Python Client for the Pupil Labs Real-Time API
"""

from __future__ import annotations

import importlib.metadata

from .device import APIPath, Device, DeviceError, StatusUpdateNotifier
from .discovery import Network, discover_devices
from .streaming import (
    AudioFrame,
    BlinkEventData,
    DualMonocularGazeData,
    EyestateGazeData,
    FixationEventData,
    FixationOnsetEventData,
    GazeData,
    RTSPData,
    RTSPAudioStreamer,
    RTSPEyeEventStreamer,
    RTSPGazeStreamer,
    RTSPImuStreamer,
    RTSPRawStreamer,
    RTSPVideoFrameStreamer,
    VideoFrame,
    receive_audio_frames,
    receive_eye_events_data,
    receive_gaze_data,
    receive_imu_data,
    receive_raw_rtsp_data,
    receive_video_frames,
)

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    "APIPath",
    "AudioFrame",
    "BlinkEventData",
    "Device",
    "DeviceError",
    "DualMonocularGazeData",
    "EyestateGazeData",
    "FixationEventData",
    "FixationOnsetEventData",
    "GazeData",
    "Network",
    "RTSPData",
    "RTSPAudioStreamer",
    "RTSPEyeEventStreamer",
    "RTSPGazeStreamer",
    "RTSPImuStreamer",
    "RTSPRawStreamer",
    "RTSPVideoFrameStreamer",
    "StatusUpdateNotifier",
    "VideoFrame",
    "__version__",
    "discover_devices",
    "imu_pb2",
    "receive_audio_frames",
    "receive_eye_events_data",
    "receive_gaze_data",
    "receive_imu_data",
    "receive_raw_rtsp_data",
    "receive_video_frames",
]
