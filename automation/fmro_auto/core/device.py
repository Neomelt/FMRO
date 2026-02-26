"""ADB device manager for emulator/device control via uiautomator2."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

import uiautomator2 as u2

from fmro_auto.core.config import settings

logger = logging.getLogger(__name__)


class DeviceManager:
    """Manage an Android device/emulator via ADB + uiautomator2."""

    def __init__(self, serial: str | None = None):
        self._serial = serial or settings.adb_device_serial
        self._device: u2.Device | None = None

    def connect(self) -> u2.Device:
        if self._serial:
            logger.info("Connecting to device: %s", self._serial)
            self._device = u2.connect(self._serial)
        else:
            logger.info("Connecting to default device")
            self._device = u2.connect()
        info = self._device.info
        logger.info(
            "Connected: %s (%sx%s)",
            info.get("productName", "unknown"),
            info.get("displayWidth"),
            info.get("displayHeight"),
        )
        return self._device

    @property
    def device(self) -> u2.Device:
        if self._device is None:
            raise RuntimeError("Device not connected. Call connect() first.")
        return self._device

    # -- ADB raw ----------------------------------------------------------
    @staticmethod
    def adb_devices() -> list[str]:
        result = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().split("\n")[1:]
        return [line.split("\t")[0] for line in lines if "\tdevice" in line]

    @staticmethod
    def is_adb_available() -> bool:
        try:
            result = subprocess.run(
                ["adb", "version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    # -- Screen interaction -----------------------------------------------
    def screenshot(self, save_path: str | None = None) -> Path:
        img = self.device.screenshot()
        out = Path(save_path or f"{settings.output_dir}/screenshot.png")
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out))
        logger.info("Screenshot saved: %s", out)
        return out

    def tap(self, x: int, y: int) -> None:
        self.device.click(x, y)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> None:
        self.device.swipe(x1, y1, x2, y2, duration=duration)

    def find_element(self, **kwargs: Any) -> Any:
        return self.device(**kwargs)

    def wait_element(self, timeout: float = 10.0, **kwargs: Any) -> bool:
        el = self.device(**kwargs)
        return el.wait(timeout=timeout)

    def input_text(self, text: str, **find_kwargs: Any) -> None:
        el = self.find_element(**find_kwargs)
        el.set_text(text)

    # -- App management ---------------------------------------------------
    def launch_app(self, package: str, activity: str | None = None) -> None:
        if activity:
            self.device.app_start(package, activity)
        else:
            self.device.app_start(package)

    def stop_app(self, package: str) -> None:
        self.device.app_stop(package)

    def current_app(self) -> dict[str, str]:
        info = self.device.app_current()
        return {"package": info.get("package", ""), "activity": info.get("activity", "")}
