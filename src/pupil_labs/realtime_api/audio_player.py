import logging
import threading
from typing import Any

import numpy as np
import numpy.typing as npt
import sounddevice as sd


class RingBuffer:
    """A highly efficient, fixed-size ring buffer for NumPy arrays."""

    def __init__(
        self,
        capacity: int,
        dtype: npt.DTypeLike,
        channels: int = 1,
        prime: bool = False,
    ):
        """Initialize a pre-allocated, empty buffer.

        Args:
            capacity: The maximum number of samples the buffer can hold.
            dtype: The NumPy data type of the samples.
            channels: The number of channels.
            prime: If True, the buffer starts full of readable silence.
                   If False, it starts logically empty.

        """
        self._buffer = np.zeros((capacity, channels), dtype=dtype)
        self._capacity = capacity
        self._write_head = 0
        self._read_head = 0
        self._size = capacity if prime else 0
        self._lock = threading.Lock()

    def write(self, data: npt.NDArray) -> None:
        """Write data to the buffer, overwriting the oldest data if full.

        Args:
            data: A NumPy array of data to write.

        """
        with self._lock:
            num_samples = len(data)
            if num_samples == 0:
                return

            if num_samples > self._capacity:
                data = data[-self._capacity :]
                num_samples = self._capacity

            write_pos = self._write_head
            space_to_end = self._capacity - write_pos

            if num_samples <= space_to_end:
                self._buffer[write_pos : write_pos + num_samples] = data
            else:
                part1_size = space_to_end
                part2_size = num_samples - part1_size
                self._buffer[write_pos:] = data[:part1_size]
                self._buffer[:part2_size] = data[part1_size:]

            self._write_head = (write_pos + num_samples) % self._capacity
            self._size = min(self._size + num_samples, self._capacity)

            if self._size == self._capacity:
                self._read_head = self._write_head

    def read(self, num_samples: int) -> npt.NDArray:
        """Read a specific number of samples from the buffer.

        Args:
            num_samples: The number of samples to read.

        Returns:
            A NumPy array containing the requested samples.

        """
        with self._lock:
            readable_samples = min(num_samples, self._size)
            if readable_samples == 0:
                return np.array([], dtype=self._buffer.dtype).reshape(-1, 1)

            read_pos = self._read_head
            space_to_end = self._capacity - read_pos

            if readable_samples <= space_to_end:
                result = self._buffer[read_pos : read_pos + readable_samples]
            else:
                part1_size = space_to_end
                part2_size = readable_samples - part1_size
                result = np.concatenate((
                    self._buffer[read_pos:],
                    self._buffer[:part2_size],
                ))

            self._read_head = (read_pos + readable_samples) % self._capacity
            self._size -= readable_samples
            return result

    @property
    def size(self) -> int:
        """Return the current number of readable samples in the buffer."""
        with self._lock:
            return self._size


class AudioPlayer(threading.Thread):
    """A threaded, low-latency audio player using a shared RingBuffer."""

    def __init__(self, samplerate: int, channels: int, dtype: str = "int16"):
        super().__init__(daemon=True)
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype

        self._stop_event = threading.Event()
        self._buffer = RingBuffer(
            capacity=1024,
            dtype=np.int16,
            channels=channels,
        )
        self.stream: sd.OutputStream | None = None

    def _callback(
        self, outdata: npt.NDArray[np.int16], frames: int, *args: Any
    ) -> None:
        """Retrieve frames to play from the buffer."""
        audio_data = self._buffer.read(frames)
        num_played = len(audio_data)
        outdata[:num_played] = audio_data
        if num_played < frames:
            outdata[num_played:] = 0

    def run(self) -> None:
        """Run the main entrypoint for the thread."""
        try:
            self.stream = sd.OutputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype=self.dtype,
                callback=self._callback,
                blocksize=0,  # Let the device choose the optimal size for low latency
                latency="low",
            )
            with self.stream:
                logging.debug("Audio stream started.")
                self._stop_event.wait()  # Wait until the close() method is called
        except Exception:
            logging.exception("Error in audio thread.")
        finally:
            logging.debug("Audio stream closed.")

    def add_data(self, data: npt.NDArray[np.int16]) -> None:
        """Directly write data to the shared RingBuffer."""
        self._buffer.write(data)

    def get_buffer_size(self) -> int:
        """Get the current number of samples in the buffer for debugging."""
        return self._buffer.size

    def close(self) -> None:
        """Signal the thread to stop and clean up resources."""
        logging.debug("Closing audio player...")
        self._stop_event.set()
        self.join()  # Wait for the thread to finish
        logging.info("Audio player closed.")
