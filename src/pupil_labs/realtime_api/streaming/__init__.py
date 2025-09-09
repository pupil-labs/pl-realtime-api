from typing import TypeVar

from pupil_labs.neon_recording.stream.imu.imu_pb2 import ImuPacket  # type: ignore

from .base import (
    RTSPData,
    RTSPRawStreamer,
    SDPDataNotAvailableError,
    receive_raw_rtsp_data,
)
from .eye_events import (
    BlinkEventData,
    FixationEventData,
    FixationOnsetEventData,
    RTSPEyeEventStreamer,
    receive_eye_events_data,
)
from .gaze import (
    DualMonocularGazeData,
    EyestateEyelidGazeData,
    EyestateGazeData,
    GazeData,
    RTSPGazeStreamer,
    receive_gaze_data,
)
from .imu import IMUData, RTSPImuStreamer, receive_imu_data
from .video import RTSPVideoFrameStreamer, VideoFrame, receive_video_frames
from .audio import RTSPAudioStreamer, AudioFrame, receive_audio_frames

RTSPStreamerType = TypeVar("RTSPStreamerType", bound="RTSPRawStreamer")
"""Type annotation for RTSP Streamer classes"""

__all__ = [
    "AudioFrame",
    "BlinkEventData",
    "DualMonocularGazeData",
    "EyestateEyelidGazeData",
    "EyestateGazeData",
    "FixationEventData",
    "FixationOnsetEventData",
    "GazeData",
    "IMUData",
    "ImuPacket",
    "RTSPData",
    "RTSPAudioStreamer",
    "RTSPEyeEventStreamer",
    "RTSPGazeStreamer",
    "RTSPImuStreamer",
    "RTSPRawStreamer",
    "RTSPVideoFrameStreamer",
    "SDPDataNotAvailableError",
    "VideoFrame",
    "receive_audio_frames",
    "receive_eye_events_data",
    "receive_gaze_data",
    "receive_imu_data",
    "receive_raw_rtsp_data",
    "receive_video_frames",
]
