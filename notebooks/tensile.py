"""Helpers for the MTS tensile tests: find the data files, load a test, compute stress and strain.

Keep this file in the same folder as the notebooks, then in a notebook:

    from tensile import list_test_files, load_test, stress_strain
"""
from __future__ import annotations

import os

import pandas as pd

DATA_SUFFIX = ".xlsx"  # MTS exports are Excel workbooks
LOCK_PREFIX = "~$"  # Excel lock files: exist only while a workbook is open
DEFAULT_LOAD_THRESHOLD_N = 10.0  # loads below this are preload, not test data


def list_test_files(folder: str) -> list[str]:
    """List the MTS data files in a folder, in a fixed order.

    Skips anything that is not an Excel workbook (``.DS_Store``, ``Thumbs.db``)
    and Excel's ``~$`` lock files, so ``list_test_files(folder)[0]`` is the same
    file on every computer.

    Parameters
    ----------
    folder : str
        Folder holding the ``.xlsx`` exports, e.g. ``os.path.join("..", "data", "MTS_metals")``.

    Returns
    -------
    list of str
        File names (not full paths), sorted alphabetically.
    """
    return sorted(
        f for f in os.listdir(folder)
        if f.endswith(DATA_SUFFIX) and not f.startswith(LOCK_PREFIX)
    )


def load_test(path: str) -> tuple[pd.Series, pd.DataFrame]:
    """Read one MTS export: the specimen metadata and the load-displacement record.

    Parameters
    ----------
    path : str
        Full path to the ``.xlsx`` file.

    Returns
    -------
    metadata : pandas.Series
        Specimen geometry and MTS results (Sheet1), indexed by column name,
        e.g. ``metadata["Area (mm²)"]``.
    data : pandas.DataFrame
        The time series (Sheet2): ``Load (N)``, ``Crosshead (mm)``,
        ``Extensometer (mm)``, ``Time (sec)``.
    """
    metadata = pd.read_excel(path, sheet_name="Sheet1").iloc[0]
    data = pd.read_excel(path, sheet_name="Sheet2", header=1)
    return metadata, data


def stress_strain(data: pd.DataFrame, metadata: pd.Series,
                  load_threshold: float = DEFAULT_LOAD_THRESHOLD_N) -> pd.DataFrame:
    """Engineering stress and strain, with the preload removed.

    Parameters
    ----------
    data : pandas.DataFrame
        Time series from :func:`load_test`.
    metadata : pandas.Series
        Metadata from :func:`load_test`; supplies the area and the gauge length.
    load_threshold : float, optional
        Rows with ``Load (N)`` at or below this value are dropped as preload.

    Returns
    -------
    pandas.DataFrame
        A copy of the loaded rows with two new columns: ``Stress (MPa)`` (load / area)
        and ``Strain`` (extensometer / gauge length, dimensionless).
    """
    area_mm2 = metadata["Area (mm²)"]
    gauge_length_mm = metadata["Initial Marked Gage Length (mm)"]
    curve = data[data["Load (N)"] > load_threshold].copy()
    curve["Stress (MPa)"] = curve["Load (N)"] / area_mm2
    curve["Strain"] = curve["Extensometer (mm)"] / gauge_length_mm
    return curve


def test_label(filename: str) -> str:
    """Plot label from a file name such as ``4_1018_run249.xlsx`` -> ``1018 (test 4)``."""
    test_number, material = filename.split("_")[:2]
    return f"{material} (test {test_number})"
