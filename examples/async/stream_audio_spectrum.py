import asyncio
import contextlib
import logging
import os

import librosa
import numpy as np
from rich.align import Align
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from pupil_labs.realtime_api import (
    Device,
    Network,
    receive_audio_frames,
)


class TerminalAudioBar:
    def __init__(self, target_freq, color, max_height=24, min_level=0, max_level=1.0):
        self.target_freq = target_freq
        self.color = color
        self.min_height = 1
        self.max_height = max_height
        self.height = self.min_height
        self.min_level = min_level
        self.max_level = max_level
        level_range = self.max_level - self.min_level
        height_range = self.max_height - self.min_height
        self.__level_height_ratio = height_range / level_range if level_range else 1.0

    def update(self, dt, level):
        desired_height = self.min_height + (level * self.__level_height_ratio)
        speed = (desired_height - self.height) / 0.1
        self.height += speed * dt
        self.height = np.clip(self.height, self.min_height, self.max_height)


def generate_linear_spectrum(audio_chunk, sample_rate, bars, dt):
    """Render a linear, vertically symmetric bar spectrum."""
    audio_chunk = np.squeeze(audio_chunk).astype(np.float32)
    if audio_chunk.size == 0:
        return ""

    stft_data = librosa.stft(audio_chunk)
    stft_magnitude = np.abs(stft_data)
    n_fft = (stft_magnitude.shape[0] - 1) * 2
    freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=n_fft)
    freqs = freqs[: stft_magnitude.shape[0]]

    for bar in bars:
        freq_index = np.argmin(np.abs(freqs - bar.target_freq))
        level = np.mean(stft_magnitude[freq_index, :])
        bar.update(dt, level)

    term_size_obj = os.get_terminal_size()
    height = min(term_size_obj.lines, 40)

    center_y = height // 2
    output_text = Text()

    for row_idx in range(height):
        row_text = Text()
        for bar in bars:
            half_height = bar.height / 2
            is_filled_down = center_y <= row_idx < center_y + half_height
            is_filled_up = center_y > row_idx >= center_y - half_height

            if is_filled_up or is_filled_down:
                row_text.append("█", style=bar.color)
            else:
                row_text.append(" ")

        output_text.append(row_text)
        output_text.append("\n")

    return output_text


async def main():
    async with Network() as network:
        dev_info = await network.wait_for_new_device(timeout_seconds=5)
    if dev_info is None:
        print("No device could be found! Abort")
        return

    async with Device.from_discovered_device(dev_info) as device:
        print(f"Getting status information from {device}")

        status = await device.get_status()

        sensor_audio = status.direct_audio_sensor()
        if not sensor_audio.connected:
            print(f"Audio sensor is not connected to {device}")
            return

        audio_generator = receive_audio_frames(sensor_audio.url, run_loop=True)
        # Prime the generator to get the first frame for parameters
        first_frame = await anext(audio_generator)
        print(
            f"Audio stream parameters: "
            f"Sample Rate: {first_frame.av_frame.sample_rate}, "
            f"Channels: {first_frame.av_frame.layout.nb_channels}, "
            f"Layout: {first_frame.av_frame.layout.name}"
        )

        frequencies = np.logspace(
            np.log10(100), np.log10(first_frame.av_frame.sample_rate / 2), num=100
        )

        bars = [
            TerminalAudioBar(
                target_freq=freq,
                color="cyan",
            )
            for i, freq in enumerate(frequencies)
        ]
        last_ts = first_frame.timestamp_unix_seconds
        with Live(auto_refresh=False, screen=True, vertical_overflow="visible") as live:
            async for audio_frame in receive_audio_frames(
                sensor_audio.url, run_loop=True
            ):
                dt = audio_frame.timestamp_unix_seconds - last_ts
                last_ts = audio_frame.timestamp_unix_seconds
                aframe_ndarray = audio_frame.to_ndarray()

                spectrum = generate_linear_spectrum(
                    aframe_ndarray,
                    sample_rate=audio_frame.av_frame.sample_rate,
                    bars=bars,
                    dt=dt,
                )
                display_panel = Panel(
                    Align.center(spectrum, vertical="middle"),
                    title="[bold cyan]Live Audio Waveform[/bold cyan]",
                    border_style="magenta",
                    padding=(1, 1),
                )
                live.update(display_panel, refresh=True)

        try:
            # Keep the main asyncio loop running until interrupted
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logging.info("Main task cancelled.")
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received.")


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
