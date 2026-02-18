import os
import importlib
import pkgutil

from typing import Callable

from system_monitor.metric_types import Message

listeners: list[Callable[[Message], None]] = []

current_dir = os.path.dirname(__file__)

for _, model_name, _ in pkgutil.iter_modules([current_dir]):
    if model_name == "__init__":
        continue
    module = importlib.import_module("." + model_name, package=__name__)
    handler = getattr(module, "handle_message")
    listeners.append(handler)
