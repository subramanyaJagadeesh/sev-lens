from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

LOG_LEVEL = os.getenv("SEVLENS_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger().setLevel(LOG_LEVEL)

from .queue import RedisAnalysisWorker


async def main() -> None:
    worker = RedisAnalysisWorker()
    worker.analysis_engine.ensure_log_store_ready()
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
