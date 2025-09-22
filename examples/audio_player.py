import contextlib
import logging
import multiprocessing as mp
import queue

import numpy as np
import numpy.typing as npt

try:
    import sounddevice as sd
except ImportError:
    raise ImportError(
        "sounddevice library not found. Please install with: pip install sounddevice to"
        "run this example or install pl-realtime with examples extras: "
        "pip install pupil-labs-realtime-api[examples]"
        "uv pip install pupil-labs-realtime-api --group examples"
    ) from None


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

    def write(self, data: npt.NDArray) -> None:
        """Write data to the buffer, overwriting the oldest data if full.

        Args:
            data: A NumPy array of data to write.

        """
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
        return self._size


class AudioPlayer(mp.Process):
    """Self-contained Audio Player (own process) using a ring buffer and SoundDevice"""

    def __init__(self, samplerate: int, channels: int, dtype: str = "int16"):
        with contextlib.suppress(RuntimeError):
            mp.set_start_method("spawn")
        super().__init__()
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype

        self._queue: mp.Queue = mp.Queue()
        self._stop_event = mp.Event()
        self._buffer = RingBuffer(
            capacity=samplerate,
            dtype=np.int16,
            channels=channels,
        )

    def _callback(self, outdata: npt.NDArray[np.int16], frames: int, *args) -> None:  # type: ignore
        """Retrieve frames to play from the buffer."""
        audio_data = self._buffer.read(frames)
        num_played = len(audio_data)
        outdata[:num_played] = audio_data
        if num_played < frames:
            outdata[num_played:] = 0

    def run(self) -> None:
        """Run the main entrypoint for the audio playback process."""
        try:
            stream = sd.OutputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype=self.dtype,
                callback=self._callback,
                blocksize=0,
                latency="low",
            )
            with stream:
                logging.debug("Audio stream started.")
                while not self._stop_event.is_set():
                    try:
                        data = self._queue.get(timeout=0.1)
                        if data is None:
                            break
                        self._buffer.write(data)
                    except queue.Empty:
                        continue
        except Exception:
            logging.exception("Error in audio thread.")
        finally:
            logging.debug("Audio stream closed.")

    def add_data(self, data: npt.NDArray[np.int16]) -> None:
        """Add a ready-to-play numpy array to the queue."""
        self._queue.put(data)

    def close(self) -> None:
        """Stop the audio playback thread and waits for it to exit."""
        logging.debug("Closing audio player...")
        self._stop_event.set()
        self._queue.put(None)  # Send sentinel to unblock the queue.get()
        self.join()  # Wait for the process to terminate
        logging.info("Audio player closed.")
