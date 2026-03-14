"""Tests for device merge and processing utility functions."""
import pytest
from app.processing import _extract_metadata, _parse_timestamp, detect_quarters


class TestExtractMetadata:
    def test_parses_multiple_kv_pairs(self):
        content = "# device_id=A3F7,player_name=Alice_Pienaar\ntimestamp,ax\n1000,0.1\n"
        meta = _extract_metadata(content)
        assert meta["device_id"] == "A3F7"
        assert meta["player_name"] == "Alice_Pienaar"

    def test_single_kv_backward_compat(self):
        content = "# device_id=B2C4\ntimestamp,ax\n1000,0.1\n"
        meta = _extract_metadata(content)
        assert meta["device_id"] == "B2C4"
        assert "player_name" not in meta

    def test_missing_metadata(self):
        content = "timestamp,ax\n1000,0.1\n"
        meta = _extract_metadata(content)
        assert meta == {}


class TestParseTimestamp:
    def test_epoch_seconds(self):
        ts = _parse_timestamp("1710410400.0")  # normal epoch
        assert ts is not None
        assert abs(ts - 1710410400.0) < 1

    def test_epoch_milliseconds(self):
        ts = _parse_timestamp("1710410400000")
        assert ts is not None
        assert abs(ts - 1710410400.0) < 1

    def test_iso_8601(self):
        ts = _parse_timestamp("2026-03-14T10:00:00+00:00")
        assert ts is not None
        assert ts > 0

    def test_invalid_returns_none(self):
        assert _parse_timestamp("not_a_timestamp") is None
        assert _parse_timestamp("") is None


class TestDetectQuarters:
    def test_clear_idle_periods(self):
        """Build rows with active-idle-active pattern → should find 2 quarters."""
        base = 1700000000  # epoch seconds > 1e9 so _parse_timestamp treats as seconds
        rows_player = []
        # Q1: 0-600s active
        for t in range(0, 600):
            rows_player.append({"timestamp": str(base + t), "speed": "8.0"})
        # Break: 600-720s idle
        for t in range(600, 720):
            rows_player.append({"timestamp": str(base + t), "speed": "0.0"})
        # Q2: 720-1320s active
        for t in range(720, 1320):
            rows_player.append({"timestamp": str(base + t), "speed": "8.0"})

        quarters = detect_quarters([rows_player], base, base + 1320)
        assert len(quarters) == 2
        assert quarters[0]["end"] < quarters[1]["start"]

    def test_continuous_play(self):
        """No idle periods → single quarter."""
        base = 1700000000
        rows = [{"timestamp": str(base + t), "speed": "8.0"} for t in range(0, 600)]
        quarters = detect_quarters([rows], base, base + 600)
        assert len(quarters) == 1

    def test_short_duration(self):
        """Duration < 60s → single quarter."""
        base = 1700000000
        rows = [{"timestamp": str(base + t), "speed": "8.0"} for t in range(0, 30)]
        quarters = detect_quarters([rows], base, base + 30)
        assert len(quarters) == 1
