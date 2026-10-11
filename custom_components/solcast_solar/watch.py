"""Solcast file monitoring."""

from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime as dt
from enum import IntEnum
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Any

try:
    from asyncinotify import Inotify, Mask

    NATIVE_WATCH_AVAILABLE: bool = True
except ImportError:
    Inotify = None
    Mask = None
    NATIVE_WATCH_AVAILABLE = False

from homeassistant.core import CALLBACK_TYPE
from homeassistant.helpers.event import async_call_later

from .const import (
    ADVANCED_RELOAD_ON_ADVANCED_CHANGE,
    ADVANCED_WATCH_FILES_POLL_INTERVAL,
    CONFIG_DISCRETE_NAME,
    CONFIG_FOLDER_DISCRETE,
    DEFAULT_WATCH_FILES_POLL_INTERVAL,
    SITE_DAMP,
    TASK_WATCH_ADVANCED,
    TASK_WATCH_ADVANCED_FILE_CHANGE,
    TASK_WATCH_DAMPENING,
    TASK_WATCH_DAMPENING_FILE_CHANGE,
)

if TYPE_CHECKING:
    from .coordinator import SolcastUpdateCoordinator

from .log import get_logger

_LOGGER = get_logger(__name__)


class Change(IntEnum):
    """File change types emitted by the native watcher."""

    added = 1
    modified = 2
    deleted = 3


def _mask_to_change(mask: Any) -> Change | None:
    """Map inotify masks to change types used by the watcher logic."""
    if Mask is None:
        return None

    if mask & (Mask.DELETE | Mask.DELETE_SELF | Mask.MOVED_FROM):
        return Change.deleted
    # Treat close-write and move-into-place as meaningful updates and ignore
    # noisier intermediate events (e.g. MODIFY/ATTRIB bursts).
    if mask & (Mask.CLOSE_WRITE | Mask.MOVED_TO):
        return Change.modified
    return None


async def awatch(
    path: str,
    watch_filter: Any = None,
    debounce: int = 50,
    step: int = 10,
    stop_event: Event | None = None,
) -> Any:
    """Yield native filesystem change events from inotify.

    The `debounce` and `step` parameters are accepted for API compatibility.
    """
    del debounce, step

    if Inotify is None or Mask is None:
        return

    inotify = Inotify()
    try:
        inotify.add_watch(
            path,
            Mask.MOVED_TO | Mask.DELETE | Mask.DELETE_SELF | Mask.MOVED_FROM | Mask.CLOSE_WRITE | Mask.CREATE,
        )

        async for event in inotify:
            if stop_event is not None and stop_event.is_set():
                break

            change_type = _mask_to_change(event.mask)
            if change_type is None:
                continue

            changed_path = str(getattr(event, "path", Path(path) / event.name))
            if watch_filter is not None and not watch_filter(change_type, changed_path):
                continue

            yield {(change_type, changed_path)}
    finally:
        inotify.close()


class FileWatcher:
    """File monitoring for the Solcast Solar integration."""

    def __init__(self, coordinator: SolcastUpdateCoordinator) -> None:
        """Initialise the file watcher.

        Arguments:
            coordinator: The update coordinator.

        """
        self.coordinator = coordinator
        self._pending_restart: CALLBACK_TYPE | None = None

    def _awatch_kwargs(self, stop_event: Event | None) -> dict[str, Any]:
        """Return common watcher arguments for responsive shutdown."""
        return {
            "debounce": 50,
            "step": 10,
            "stop_event": stop_event,
        }

    def _start_managed_task(self, task_name: str, coro: Any) -> None:
        """Start a task whose cancellation also stops its watcher iterator."""
        coordinator = self.coordinator
        stop_event = Event()
        task = asyncio.create_task(coro(stop_event))

        def cancel() -> None:
            stop_event.set()
            task.cancel()

        coordinator.tasks[task_name] = cancel

    def _path_exists(self, file_path: str) -> bool:
        """Return whether a path exists, tolerating transient filesystem races."""
        try:
            return Path(file_path).exists()
        except OSError:
            return False

    def _poll_interval(self) -> float:
        """Return polling interval for fallback mode from advanced options."""
        advanced_options = getattr(getattr(self.coordinator, "solcast", None), "advanced_options", {})
        interval = advanced_options.get(ADVANCED_WATCH_FILES_POLL_INTERVAL, DEFAULT_WATCH_FILES_POLL_INTERVAL)
        if not isinstance(interval, int | float) or interval <= 0:
            return DEFAULT_WATCH_FILES_POLL_INTERVAL
        return float(interval)

    async def setup(self) -> None:
        """Set up file watcher tasks."""
        coordinator = self.coordinator

        if not NATIVE_WATCH_AVAILABLE:
            _LOGGER.warning("inotify backend is not available, using polling fallback for file monitoring")

        self._start_managed_task(
            TASK_WATCH_ADVANCED_FILE_CHANGE,
            lambda stop_event: self.watch_for_file(
                TASK_WATCH_ADVANCED,
                coordinator.file_advanced,
                self.watch_advanced_file,
                process_on_add=True,
                stop_event=stop_event,
            ),
        )
        if not coordinator.solcast.options.auto_dampen:
            self._start_managed_task(
                TASK_WATCH_DAMPENING_FILE_CHANGE,
                lambda stop_event: self.watch_for_file(
                    TASK_WATCH_DAMPENING,
                    coordinator.file_dampening,
                    self.watch_dampening_file,
                    process_on_add=False,
                    stop_event=stop_event,
                ),
            )
        else:
            _LOGGER.debug("Not monitoring dampening file, auto-dampening is enabled")

    async def _restart(self, _called_at: dt | None = None) -> None:
        """Restart the integration to apply advanced configuration changes."""
        self._pending_restart = None
        coordinator = self.coordinator
        await coordinator.solcast.tasks_cancel()
        await coordinator.tasks_cancel()
        await coordinator.hass.config_entries.async_reload(coordinator.entry.entry_id)

    def _watch_dir(self, file_path: str) -> str:
        """Return the directory to watch for a given file path."""
        if CONFIG_FOLDER_DISCRETE:
            return f"{self.coordinator.hass.config.config_dir}/{CONFIG_DISCRETE_NAME}"
        return str(Path(file_path).parent)

    async def watch_for_file(
        self,
        task: str,
        file_path: str,
        handler: Any,
        process_on_add: bool = True,
        stop_event: Event | None = None,
    ) -> None:
        """Watch for file creation and start the handler task when the file appears."""
        coordinator = self.coordinator

        if self._path_exists(file_path):
            self._start_managed_task(task, lambda handler_stop_event: handler(False, handler_stop_event))
            _LOGGER.debug("Running task %s", task)

        if NATIVE_WATCH_AVAILABLE and awatch is not None:
            try:
                async for changes in awatch(
                    self._watch_dir(file_path),
                    watch_filter=lambda change, path: path == file_path,
                    **self._awatch_kwargs(stop_event),
                ):
                    for change_type, changed_path in changes:
                        if (
                            change_type in (Change.added, Change.modified)
                            and changed_path == file_path
                            and coordinator.tasks.get(task) is None
                            and self._path_exists(file_path)
                        ):
                            self._start_managed_task(
                                task,
                                lambda handler_stop_event: handler(process_on_add, handler_stop_event),
                            )
                            _LOGGER.debug("Running task %s", task)
                return
            except OSError:
                _LOGGER.debug("Native watch unavailable for %s, using polling fallback", file_path)

        while stop_event is None or not stop_event.is_set():
            await asyncio.sleep(self._poll_interval())
            if coordinator.tasks.get(task) is None and self._path_exists(file_path):
                self._start_managed_task(task, lambda handler_stop_event: handler(process_on_add, handler_stop_event))
                _LOGGER.debug("Running task %s", task)

    async def _handle_dampening_update(self, file_path: str) -> None:
        """Refresh dampening data after a file change."""
        coordinator = self.coordinator

        try:
            dampening_mtime = Path(file_path).stat().st_mtime
        except FileNotFoundError:
            return

        if coordinator.solcast.dampening.factors_mtime != dampening_mtime:
            _LOGGER.debug("Granular dampening mtime changed")
            await coordinator.solcast.dampening.refresh_granular_data()
            await coordinator.solcast.dampening.apply_forward()
            _LOGGER.debug("Recalculate forecasts and refresh sensors")
            await coordinator.solcast.build_forecast_data()
            await coordinator.update_integration_listeners()

    async def watch_dampening_file(
        self,
        initial_change: bool = False,
        stop_event: Event | None = None,
    ) -> None:
        """Watch for granular dampening JSON file modification."""
        coordinator = self.coordinator
        task = TASK_WATCH_DAMPENING
        file_path = coordinator.file_dampening

        try:
            if initial_change:
                await self._handle_dampening_update(file_path)

            use_polling = not (NATIVE_WATCH_AVAILABLE and awatch is not None)
            if not use_polling:
                try:
                    async for changes in awatch(
                        str(Path(file_path).parent),
                        watch_filter=lambda change, path: path == file_path,
                        **self._awatch_kwargs(stop_event),
                    ):
                        deleted = False
                        for change_type, _ in changes:
                            if change_type == Change.deleted:
                                deleted = True
                                break
                            if change_type in (Change.modified, Change.added):
                                await self._handle_dampening_update(file_path)
                        if deleted:
                            if self._path_exists(file_path):
                                _LOGGER.debug("Granular dampening file recreation detected, continuing to monitor %s", file_path)
                                continue
                            if coordinator.solcast.dampening.granular_serialising:
                                _LOGGER.debug("Granular dampening file write in progress, continuing to monitor %s", file_path)
                                continue
                            _LOGGER.debug("Granular dampening file deleted, no longer monitoring %s for changes", file_path)
                            coordinator.solcast.dampening.factors = {}
                            entry = coordinator.solcast.entry
                            opt = {**coordinator.solcast.entry_options}
                            opt[SITE_DAMP] = False
                            for hour in range(24):
                                opt[f"damp{hour:02}"] = coordinator.solcast.damp.get(f"{hour}", opt.get(f"damp{hour:02}", 1.0))
                            coordinator.solcast.dampening.set_allow_granular_reset(True)
                            if entry is not None:
                                coordinator.hass.config_entries.async_update_entry(entry, options=opt)
                            break
                except OSError:
                    _LOGGER.debug("Native watch unavailable for %s, using polling fallback", file_path)
                    use_polling = True

            if use_polling:
                last_exists = self._path_exists(file_path)
                last_mtime: float | None = None
                if last_exists:
                    with contextlib.suppress(OSError):
                        last_mtime = Path(file_path).stat().st_mtime

                while stop_event is None or not stop_event.is_set():
                    await asyncio.sleep(self._poll_interval())

                    exists = self._path_exists(file_path)
                    if exists:
                        with contextlib.suppress(OSError):
                            mtime = Path(file_path).stat().st_mtime
                            if last_mtime is None or mtime != last_mtime:
                                await self._handle_dampening_update(file_path)
                                last_mtime = mtime
                    elif last_exists:
                        if coordinator.solcast.dampening.granular_serialising:
                            _LOGGER.debug("Granular dampening file write in progress, continuing to monitor %s", file_path)
                        else:
                            _LOGGER.debug("Granular dampening file deleted, no longer monitoring %s for changes", file_path)
                            coordinator.solcast.dampening.factors = {}
                            entry = coordinator.solcast.entry
                            opt = {**coordinator.solcast.entry_options}
                            opt[SITE_DAMP] = False
                            for hour in range(24):
                                opt[f"damp{hour:02}"] = coordinator.solcast.damp.get(
                                    f"{hour}",
                                    opt.get(f"damp{hour:02}", 1.0),
                                )
                            coordinator.solcast.dampening.set_allow_granular_reset(True)
                            if entry is not None:
                                coordinator.hass.config_entries.async_update_entry(entry, options=opt)
                            break

                    last_exists = exists
        finally:
            if coordinator.tasks.get(task) is not None:
                if stop_event is None:
                    coordinator.tasks[task]()
                coordinator.tasks.pop(task)
                _LOGGER.debug("Cancelled task %s", task)

    async def _handle_advanced_update(self) -> None:
        """Reload advanced options after a file change."""
        coordinator = self.coordinator

        change = await coordinator.solcast.advanced_opt.read_advanced_options()
        if change and coordinator.solcast.advanced_options.get(ADVANCED_RELOAD_ON_ADVANCED_CHANGE, False):
            _LOGGER.debug("Advanced options changed, restarting")
            if self._pending_restart is not None:
                self._pending_restart()
            self._pending_restart = async_call_later(coordinator.hass, 1, self._restart)

    async def watch_advanced_file(
        self,
        initial_change: bool = False,
        stop_event: Event | None = None,
    ) -> None:
        """Watch for advanced options JSON file modification."""
        coordinator = self.coordinator
        task = TASK_WATCH_ADVANCED
        file_path = coordinator.file_advanced

        try:
            _LOGGER.debug("Monitoring %s", file_path)
            if initial_change:
                await self._handle_advanced_update()

            use_polling = not (NATIVE_WATCH_AVAILABLE and awatch is not None)
            if not use_polling:
                try:
                    async for changes in awatch(
                        str(Path(file_path).parent),
                        watch_filter=lambda change, path: path == file_path,
                        **self._awatch_kwargs(stop_event),
                    ):
                        deleted = False
                        for change_type, _ in changes:
                            if change_type == Change.deleted:
                                deleted = True
                                break
                            if change_type in (Change.modified, Change.added):
                                await self._handle_advanced_update()
                        if deleted:
                            _LOGGER.debug("Advanced options file deleted, no longer monitoring %s for changes", file_path)
                            coordinator.solcast.advanced_opt.set_default_advanced_options()
                            break
                except OSError:
                    _LOGGER.debug("Native watch unavailable for %s, using polling fallback", file_path)
                    use_polling = True

            if use_polling:
                last_exists = self._path_exists(file_path)
                last_mtime: float | None = None
                if last_exists:
                    with contextlib.suppress(OSError):
                        last_mtime = Path(file_path).stat().st_mtime

                while stop_event is None or not stop_event.is_set():
                    await asyncio.sleep(self._poll_interval())

                    exists = self._path_exists(file_path)
                    if exists:
                        with contextlib.suppress(OSError):
                            mtime = Path(file_path).stat().st_mtime
                            if last_mtime is None or mtime != last_mtime:
                                await self._handle_advanced_update()
                                last_mtime = mtime
                    elif last_exists:
                        _LOGGER.debug("Advanced options file deleted, no longer monitoring %s for changes", file_path)
                        coordinator.solcast.advanced_opt.set_default_advanced_options()
                        break

                    last_exists = exists
        finally:
            if coordinator.tasks.get(task) is not None:
                if stop_event is None:
                    coordinator.tasks[task]()
                coordinator.tasks.pop(task)
                _LOGGER.debug("Cancelled task %s", task)
