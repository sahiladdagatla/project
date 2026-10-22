"""
Data Provenance and Quality Flags.

Section 5.1: "Represent data provenance and quality flags. Keep transport connectivity
separate from hydrological connectivity."
Section 4: "Explicit operating modes. Benchmark simulation vs Satellite observation vs Dev fixture."
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from backend.app.config import OperatingMode


class QualityFlag(BaseModel):
    """Quality and verification status of a dataset or calculation."""
    is_synthetic_fixture: bool = Field(default=False, description="True if synthetic fixture; false if benchmark/real data.")
    is_calibrated: bool = Field(default=False, description="True if physics-calibrated or ground-truth verified.")
    is_satellite_snapshot: bool = Field(default=False, description="True if periodic satellite observation.")
    missing_data_imputed: bool = Field(default=False, description="True if missing values were interpolated.")
    elevation_quality: str = Field(default="benchmark_mesh", description="Quality of elevation data ('high', 'medium', 'low').")


class ProvenanceRecord(BaseModel):
    """Complete provenance tracking record for any system output."""
    operating_mode: OperatingMode
    dataset_name: str
    dataset_doi_or_url: str
    data_version: str
    model_version: Optional[str] = None
    generated_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    quality_flags: QualityFlag = Field(default_factory=QualityFlag)
    limitations: list[str] = Field(default_factory=list)


def create_provenance(
    mode: OperatingMode,
    dataset_name: str,
    doi_or_url: str,
    version: str = "v1.0",
    model_version: Optional[str] = None,
    is_fixture: bool = False,
    is_satellite: bool = False,
    limitations: Optional[list[str]] = None
) -> ProvenanceRecord:
    """Helper factory for generating standardized provenance records."""
    flags = QualityFlag(
        is_synthetic_fixture=is_fixture,
        is_calibrated=(mode in [OperatingMode.BENCHMARK_SIMULATION, OperatingMode.RESEARCH_BENCHMARKS]),
        is_satellite_snapshot=is_satellite,
        elevation_quality="high" if mode in [OperatingMode.BENCHMARK_SIMULATION, OperatingMode.RESEARCH_BENCHMARKS] else "medium"
    )
    return ProvenanceRecord(
        operating_mode=mode,
        dataset_name=dataset_name,
        dataset_doi_or_url=doi_or_url,
        data_version=version,
        model_version=model_version,
        quality_flags=flags,
        limitations=limitations or []
    )
