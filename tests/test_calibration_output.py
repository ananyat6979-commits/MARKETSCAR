import json


def test_calibration_output_exists():
    with open("config/frozen_thresholds.json") as fh:
        cfg = json.load(fh)
    assert (
        "seed" in cfg
        and "percentiles" in cfg
        and "calibration_timestamp_utc" in cfg
    )
