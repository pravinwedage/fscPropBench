import numpy as np

THROTTLE_DISABLED = 0
THROTTLE_WAIT = 1
THROTTLE_SPEED_UP = 2
THROTTLE_PROFILE = 3


class ThrottleProfile:
    """
    Manages automated throttle sweep profiles loaded from CSV files.

    Phase state machine:
      DISABLED -> WAIT (on activate) -> SPEED_UP -> PROFILE -> DISABLED
    """

    def __init__(self, wait_before_start_time=2, initial_throttle_rate=15, freq=100):
        self.frequency = freq
        self._delta_t = 1.0 / freq
        self._wait_before_start_time = wait_before_start_time
        self._initial_throttle_rate = initial_throttle_rate

        self.throttle = 0.0
        self.phase = THROTTLE_DISABLED

        self._current_idx = 0
        self._waiting_steps = 0
        self._total_num = 0
        self._profile_data: list = []

        self._phase_actions = {
            THROTTLE_DISABLED: self._disabled_cb,
            THROTTLE_WAIT: self._wait_cb,
            THROTTLE_SPEED_UP: self._speed_up_cb,
            THROTTLE_PROFILE: self._profile_cb,
        }

    def load_throttle_profile(self, data: list):
        self._profile_data = list(data)
        self._total_num = len(self._profile_data)
        if self._total_num > 0:
            self._waiting_steps = int(self._wait_before_start_time * self.frequency)

    def activate(self):
        """Start the profile sequence (no-op if no profile loaded)."""
        if self._total_num > 0:
            self._current_idx = 0
            self.phase = THROTTLE_WAIT

    def reset(self):
        self._current_idx = 0
        self.phase = THROTTLE_DISABLED
        self.throttle = 0.0

    def update_and_get_throttle(self):
        """Advance the state machine one tick and update self.throttle."""
        self._phase_actions[self.phase]()

    def get_progress(self) -> int:
        """Return profile completion percentage (0-100)."""
        if self.phase == THROTTLE_PROFILE and self._total_num > 0:
            return int(self._current_idx / self._total_num * 100)
        return 0

    def get_count_down_time(self) -> int:
        """Return remaining wait-phase seconds."""
        return self._wait_before_start_time - int(self._current_idx * self._delta_t)

    # ── phase callbacks ──────────────────────────────────────────────────────

    def _disabled_cb(self):
        self.throttle = 0.0

    def _wait_cb(self):
        self.throttle = 0.0
        if self._current_idx <= self._waiting_steps:
            self._current_idx += 1
        else:
            self.phase = THROTTLE_SPEED_UP

    def _speed_up_cb(self):
        target = self._profile_data[0]
        if abs(self.throttle - target) < 0.03:
            self.phase = THROTTLE_PROFILE
            self._current_idx = 0
        else:
            rate = self._saturate(
                2.0 * (target - self.throttle),
                -self._initial_throttle_rate,
                self._initial_throttle_rate,
            )
            self.throttle += self._delta_t * rate

    def _profile_cb(self):
        if self._current_idx < self._total_num:
            self.throttle = self._profile_data[self._current_idx]
            self._current_idx += 1
        else:
            self.phase = THROTTLE_DISABLED
            self._current_idx = 0
            self.throttle = 0.0

    @staticmethod
    def _saturate(value, lo, hi):
        return max(lo, min(value, hi))


def generate_sine_profile(amplitude=10, frequency_hz=0.5, offset=30,
                           sampling_rate=100, duration=5):
    """Generate a sine-wave throttle profile for testing."""
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
    return (amplitude * np.sin(2 * np.pi * frequency_hz * t) + offset).tolist()
