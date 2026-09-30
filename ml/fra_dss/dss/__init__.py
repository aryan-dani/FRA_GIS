"""DSS package."""

from fra_dss.dss.engine import recommend
from fra_dss.dss.schemas import DSSRecommendation

__all__ = ["recommend", "DSSRecommendation"]
