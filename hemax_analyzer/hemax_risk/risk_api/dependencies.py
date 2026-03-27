from __future__ import annotations

import logging
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import Header, Request

logger = logging.getLogger("risk.risk_api")

DEFAULT_MODEL_PATH = Path(__file__).parent / "weights" / "model.pt"


def get_request_id(x_request_id: Optional[str] = Header(default=None)) -> str:
    return x_request_id or str(uuid.uuid4())


@lru_cache(maxsize=1)
def get_predictor():
    from .risk.inference import RiskPredictor
    logger.info(f"Loading risk predictor from {DEFAULT_MODEL_PATH}")
    predictor = RiskPredictor(DEFAULT_MODEL_PATH)
    logger.info(f"Risk predictor loaded: {len(predictor.target_names)} tasks, "
                f"{len(predictor.feature_names)} features")
    return predictor
