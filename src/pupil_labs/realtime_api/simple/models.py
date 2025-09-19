import datetime
from typing import NamedTuple

from ..streaming.audio import AudioFrame
from ..streaming.gaze import (
    GazeDataType,
)
from ..streaming.video import BGRBuffer, VideoFrame


class SimpleVideoFrame(NamedTuple):
    """A simplified video frame representation.

    This class provides a simplified representation of a video frame with
    BGR pixel data and timestamp information.
    """

    bgr_pixels: BGRBuffer
    """BGR pixel data as a NumPy array."""
    timestamp_unix_seconds: float
    """Timestamp in seconds since Unix epoch."""

    @classmethod
    def from_video_frame(cls, vf: VideoFrame) -> "SimpleVideoFrame":
        return cls(vf.bgr_buffer(), vf.timestamp_unix_seconds)

    @property
    def datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.timestamp_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        return int(self.timestamp_unix_seconds * 1e9)


# The following name can be considered technical debt from the time when there were only
# two streams (scene video and gaze) to match. When I added support for streaming eyes
# video, I thought about giving it a more descriptive name. But since this is an output
# class of the public API, I decided against it to avoid breaking possible imports.
class MatchedItem(NamedTuple):
    """A matched pair of scene video frame and gaze data.

    This class represents a scene video frame and gaze data point that
    occurred at approximately the same time.

    Note:
        The name MatchedItem is maintained for backward compatibility.
        It represents a matched pair of scene video frame and gaze data.

    """

    frame: SimpleVideoFrame
    """Scene video frame."""
    gaze: GazeDataType
    """Corresponding gaze data."""


class MatchedGazeEyesSceneItem(NamedTuple):
    """A matched triplet of scene video frame, eye video frame, and gaze data.

    This class represents scene and eye video frames along with gaze data
    that occurred at approximately the same time.
    """

    scene: SimpleVideoFrame
    """Scene video frame."""
    eyes: SimpleVideoFrame
    """Eye camera video frame."""
    gaze: GazeDataType
    """Corresponding gaze data."""


MATCHED_ITEM_LABEL = "matched_gaze_and_scene_video"
MATCHED_GAZE_EYES_LABEL = "matched_gaze_eyes_and_scene_video"
MATCHED_SCENE_AUDIO_LABEL = "matched_scene_video_and_audio"


class MatchedSceneAudioItem(NamedTuple):
    """A matched pair of scene video frame and audio data.

    This class represents a scene video frame and audio data that
    occurred at approximately the same time.
    """

    frame: SimpleVideoFrame
    """Scene video frame."""
    audio: list[AudioFrame]
    """Corresponding audio data."""
    gaze: GazeDataType
    """Corresponding gaze data."""
