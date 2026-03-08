"""Tests for CSV processing logic."""
from app.processing import _parse_rows, validate_csv, compute_metrics


SAMPLE_CSV = """timestamp,lat_filt,lng_filt,speed,ax,ay,az,sats
1000.0,-25.7479,28.2293,5.0,0.1,0.2,9.8,8
1001.0,-25.7480,28.2294,8.0,0.5,0.3,9.7,9
1002.0,-25.7481,28.2295,12.0,1.2,0.1,9.6,10
1003.0,-25.7482,28.2296,6.0,-0.3,0.2,9.8,8
1004.0,-25.7483,28.2297,0.5,0.0,0.0,9.81,7
"""


def test_parse_rows():
    rows, columns = _parse_rows(SAMPLE_CSV)
    assert len(rows) == 5
    assert "timestamp" in columns
    assert "lat_filt" in columns
    assert "speed" in columns


def test_validate_csv():
    rows, columns = _parse_rows(SAMPLE_CSV)
    flags, errors = validate_csv(rows, columns)
    assert len(errors) == 0
    assert flags.total_rows == 5
    assert flags.valid_gps_rows == 5
    assert flags.impossible_speeds == 0


def test_validate_empty():
    rows, columns = _parse_rows("timestamp\n")
    flags, errors = validate_csv(rows, columns)
    assert len(errors) == 1
    assert "empty" in errors[0].lower()


def test_validate_missing_columns():
    rows, columns = _parse_rows("foo,bar\n1,2\n")
    flags, errors = validate_csv(rows, columns)
    assert len(errors) == 1
    assert "Missing required" in errors[0]


def test_compute_metrics():
    rows, columns = _parse_rows(SAMPLE_CSV)
    metrics = compute_metrics(rows, columns)
    assert metrics["minutes_played"] > 0
    assert metrics["total_distance_m"] > 0
    assert metrics["top_speed_kmh"] == 12.0
    assert metrics["sprint_count"] >= 0
    assert metrics["movement_count"] == 5


def test_compute_metrics_no_gps():
    csv = "timestamp,speed,ax,ay,az\n1000.0,5.0,0.1,0.2,9.8\n1001.0,8.0,0.5,0.3,9.7\n"
    rows, columns = _parse_rows(csv)
    metrics = compute_metrics(rows, columns)
    assert metrics["total_distance_m"] == 0  # No GPS
    assert metrics["minutes_played"] > 0
