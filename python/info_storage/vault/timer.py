from time import monotonic


class VaultTimer:
    def __init__(self, timeout=300.0):
        if timeout <= 0:
            raise ValueError(
                "O tempo limite deve ser maior que zero."
            )

        self.timeout = timeout
        self._last_activity = None

    def start(self):
        self._last_activity = monotonic()

    def reset(self):
        self.start()

    def stop(self):
        self._last_activity = None

    def expired(self):
        if self._last_activity is None:
            return True

        elapsed = monotonic() - self._last_activity

        return elapsed >= self.timeout

    @property
    def active(self):
        return self._last_activity is not None
