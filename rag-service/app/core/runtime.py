from __future__ import annotations

from dataclasses import dataclass

from ..analysis import AnalysisEngine


@dataclass(slots=True)
class RagRuntime:
    analysis_engine: AnalysisEngine


_RUNTIME = RagRuntime(analysis_engine=AnalysisEngine())


def get_runtime() -> RagRuntime:
    return _RUNTIME
