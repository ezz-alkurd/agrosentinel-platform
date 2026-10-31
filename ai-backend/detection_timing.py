"""Continuous detection confirmation and cooldown, independent of inference."""
class Confirmer:
    def __init__(self, confirm_seconds=2.0, cooldown_seconds=30.0):
        self.confirm_seconds = confirm_seconds
        self.cooldown_seconds = cooldown_seconds
        self._since = {}
        self._last_upload = {}

    def reset_continuity(self):
        """A source interruption breaks confirmation but preserves alert cooldowns."""
        self._since.clear()

    def update(self, key, present, now):
        if not present:
            self._since.pop(key, None)
            return False
        start = self._since.setdefault(key, now)
        if now - start < self.confirm_seconds:
            return False
        last = self._last_upload.get(key)
        if last is not None and now - last < self.cooldown_seconds:
            return False
        self._last_upload[key] = now
        self._since.pop(key, None)
        return True
