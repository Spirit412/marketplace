"""Dependency injection — rodi container setup and FastAPI integration.

The container itself lives in `src.dependencies`; this module is the single
registration entry point called from `main.py` at startup.
"""

from src.dependencies import Inject, container, init_container

__all__ = ["Inject", "container", "init_container"]
