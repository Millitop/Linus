"""Extension point for optional cloud sync -- NOT implemented in v1.

The Pi is designed to work fully offline; this interface exists purely
so a future cloud-sync backend can be added without touching the core
scan/registration logic. Enabled only if SYNC_ENABLED=true, which has no
effect yet since no concrete backend is registered.
"""
from abc import ABC, abstractmethod

from app.models import LogEntry


class CloudSyncBackend(ABC):
    @abstractmethod
    def push_log_entry(self, entry: LogEntry) -> None:
        """Send a single new log entry to the remote backend."""
        raise NotImplementedError
