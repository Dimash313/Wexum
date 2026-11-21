"""Real, local resource readings; explicitly absent when unsupported."""

from dataclasses import dataclass
import os
import shutil
import time


@dataclass(frozen=True)
class ResourceSnapshot:
    process_cpu_seconds: float
    process_rss_bytes: int | None
    disk_free_bytes: int
    disk_total_bytes: int


def read_resources(*, disk_path: str = "/") -> ResourceSnapshot:
    """Observe this process and *disk_path* mount, never remote node usage.

    Linux /proc/self/statm is optional; null means unavailable rather than zero.
    Errors are returned to the operator, not hidden as fabricated metric values.
    """
    disk = shutil.disk_usage(disk_path)
    rss = None
    if os.path.exists("/proc/self/statm"):
        try:
            with open("/proc/self/statm", encoding="ascii") as statm:
                fields = statm.read(128).split()
            rss = int(fields[1]) * os.sysconf("SC_PAGE_SIZE")
        except (OSError, ValueError, IndexError):
            rss = None
    return ResourceSnapshot(time.process_time(), rss, disk.free, disk.total)
