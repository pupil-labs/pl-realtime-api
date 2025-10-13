import datetime
import time
from typing import Any

import av
import numpy as np
import speech_recognition as sr

from pupil_labs.realtime_api.simple import discover_one_device

# --- Configuration ---
# Whisper model to use. Options: "tiny", "base", "small", "medium", "large", "turbo"
WHISPER_MODEL = "tiny"

CALIBRATION_DURATION_S = 2
# How many seconds of silence indicates the end of a phrase
PAUSE_THRESHOLD_S = 1.0
# Factor to multiply ambient energy by to get the speech detection threshold
ENERGY_FACTOR = 1.5  # Increased for better silence detection with int16 audio
# Default energy threshold for int16 audio if calibration fails
DEFAULT_ENERGY_THRESHOLD = 500

resampler = av.AudioResampler(
    format="s16",  # Target format: 16-bit signed integer
    layout="mono",  # Target layout
    rate=16000,  # Target sample rate: 16kHz
)


def calculate_rms(audio_chunk: np.ndarray) -> float:
    """Calculate the Root Mean Square of an audio chunk."""
    return np.sqrt(np.mean(audio_chunk.astype(np.float64) ** 2))


def discover_device() -> Any:
    """Look for a device, connects to it, and returns the device object."""
    print("Looking for the next best device...")
    device = discover_one_device(max_search_duration_seconds=10)
    if device is None:
        print("No device found.")
        raise SystemExit(-1)
    print(f"Found device: {device}")
    return device


def get_resampled_audio(audio_frame: Any) -> np.ndarray:
    """Resample an audio frame to the target sample rate and s16le format."""
    return resampler.resample(audio_frame.av_frame)[0].to_ndarray()[0]


def calibrate_ambient_noise(
    device: Any, duration_s: int, energy_factor: float
) -> float:
    """Record a specified duration to calculate threshold for differentiating speech

    Args:
        device: The Pupil Labs device object.
        duration_s: The number of seconds to record for calibration.
        sample_rate: The target audio sample rate.
        energy_factor: The multiplier for setting the threshold above ambient noise.

    Returns:
        The calculated energy threshold.

    """
    print(f"Calibrating for ambient noise for {duration_s} seconds...")
    calibration_buffer_int16 = []

    initial_frame = None
    print("Waiting for initial audio frame to start calibration...")
    while not initial_frame:
        initial_frame = device.receive_audio_frame(timeout_seconds=1)

    initial_frame_ts = initial_frame.timestamp_unix_seconds
    calibration_end_ts = initial_frame_ts + duration_s
    current_ts = initial_frame_ts

    audio_s16le = get_resampled_audio(initial_frame)
    calibration_buffer_int16.append(audio_s16le)

    while current_ts < calibration_end_ts:
        audio_frame = device.receive_audio_frame(timeout_seconds=1)
        if audio_frame:
            current_ts = audio_frame.timestamp_unix_seconds
            audio_s16le = get_resampled_audio(audio_frame)
            calibration_buffer_int16.append(audio_s16le)

    if not calibration_buffer_int16:
        print(
            "Warning: No audio received during calibration. Using a default threshold."
        )
        return DEFAULT_ENERGY_THRESHOLD

    full_calibration_audio = np.concatenate(calibration_buffer_int16)
    ambient_energy = calculate_rms(full_calibration_audio)
    energy_threshold = ambient_energy * energy_factor
    print(f"Calibration complete. Energy threshold set to {energy_threshold:.4f}")
    return energy_threshold


def process_transcription(
    recognizer: sr.Recognizer, audio_buffer: list, model: str, timestamp: float
):
    """Transcribe a buffer of audio data using the Whisper model and prints the result.

    Args:
        recognizer: The speech_recognition.Recognizer instance.
        audio_buffer: A list of s16 audio chunks (numpy arrays).
        sample_rate: The audio sample rate.
        model: The name of the Whisper model to use.
        timestamp: The audio chunk timestamp in unix epoch sec.

    """
    if not audio_buffer:
        return

    full_audio_int16 = np.concatenate(audio_buffer)
    audio_bytes = full_audio_int16.tobytes()
    # Sample width for s16 audio is 2 bytes
    audio_data = sr.AudioData(audio_bytes, 16000, 2)

    try:
        result_text = recognizer.recognize_whisper(
            audio_data, model=model, language="en"
        )
        if result_text.strip():
            timestamp_str = datetime.datetime.fromtimestamp(timestamp).strftime(
                "%H:%M:%S"
            )
            print(f"{timestamp_str}: {result_text}")
            # Here you can detect keywords and send events.
    except sr.UnknownValueError:
        # This is expected when speech is not understood.
        pass
    except sr.RequestError as e:
        print(f"Could not request results from Whisper; {e}")


def transcription_loop(
    device: Any,
    recognizer: sr.Recognizer,
    energy_threshold: float,
    pause_threshold_s: float,
    whisper_model: str,
):
    """Transcribe audio, Speech-To-Text utility

    Listens for audio, detects speech based on an energy threshold, buffers
    the speech, and sends it for transcription after a pause.
    """
    audio_buffer = []
    is_speaking = False
    silence_started_at = None

    print("Listening for speech... Press Ctrl+C to stop.")
    while True:
        audio_frame = device.receive_audio_frame(timeout_seconds=5)
        if not audio_frame:
            continue

        audio_int16 = get_resampled_audio(audio_frame)

        current_energy = calculate_rms(audio_int16)
        is_speech = current_energy > energy_threshold

        if is_speech:
            silence_started_at = None
            is_speaking = True
            audio_buffer.append(audio_int16)
        elif is_speaking:
            if silence_started_at is None:
                silence_started_at = audio_frame.timestamp_unix_seconds

            if (
                audio_frame.timestamp_unix_seconds - silence_started_at
                > pause_threshold_s
            ):
                process_transcription(
                    recognizer,
                    audio_buffer,
                    whisper_model,
                    audio_frame.timestamp_unix_seconds,
                )
                # Reset for the next phrase
                audio_buffer.clear()
                is_speaking = False
                silence_started_at = None


def main():
    recognizer = sr.Recognizer()
    device = None
    try:
        device = discover_device()
        device.streaming_start("audio")
        time.sleep(1)  # Wait a moment for the stream to stabilize

        energy_threshold = calibrate_ambient_noise(
            device, CALIBRATION_DURATION_S, ENERGY_FACTOR
        )

        transcription_loop(
            device,
            recognizer,
            energy_threshold,
            PAUSE_THRESHOLD_S,
            WHISPER_MODEL,
        )

    except KeyboardInterrupt:
        print("\nInterruption detected.")
    finally:
        print("Stopping...")
        if device:
            device.close()
        print("Device connection closed.")


if __name__ == "__main__":
    main()
