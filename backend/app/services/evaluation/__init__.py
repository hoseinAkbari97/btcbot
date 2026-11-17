"""Read-only statistical evaluation of persisted backtest runs.

The package consumes stored experiment results through a documented interface
and never re-runs the engine, edits a stored run, or touches reserved data. See
``docs/STRATEGY_EVALUATION.md`` for the methods, their assumptions and the
claims this package refuses to make.
"""

from __future__ import annotations
