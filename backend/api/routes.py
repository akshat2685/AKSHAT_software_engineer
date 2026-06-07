from __future__ import annotations

from typing import Any, Dict, Protocol


class AkshatController(Protocol):
    def snapshot(self) -> Dict[str, Any]:
        ...

    def submit(self, prompt: str) -> Dict[str, Any]:
        ...


def dashboard_status(controller: AkshatController) -> Dict[str, Any]:
    return controller.snapshot()


def submit_software_task(controller: AkshatController, task: str) -> Dict[str, Any]:
    return controller.submit(task)
