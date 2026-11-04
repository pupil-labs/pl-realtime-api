import math
from types import SimpleNamespace

import pytest
from aiortsp.rtcp.parser import SR

from pupil_labs.realtime_api.streaming.base import (
    _UnknownClockoffsetError,
    _WallclockRTSPReader,
)


@pytest.fixture
def reader(monkeypatch):
    instance = _WallclockRTSPReader("rtsp://example.invalid/stream")
    monkeypatch.setattr(instance, "get_rtpmap", lambda: {"clockRate": 90000})
    return instance


@pytest.mark.parametrize(
    "clock_rate,report_counter,report_time,packet_counter,expected",
    [
        (90000, 900000, 1700000000.0, 990000, 1700000001.0),
        (90000, 900000, 1700000000.0, 810000, 1699999999.0),
        (90000, 900000, 1700000000.0, 900000, 1700000000.0),
        (90000, 4294799520, 1793794350.950418, 232, 1793794352.8171735),
        (90000, 232, 1793794352.8171735, 4294799520, 1793794350.950418),
        (1000, 2**32 - 16, 1000.0, 16, 1000.032),
    ],
)
def test_absolute_timestamp(
    reader,
    monkeypatch,
    clock_rate,
    report_counter,
    report_time,
    packet_counter,
    expected,
):
    monkeypatch.setattr(reader, "get_rtpmap", lambda: {"clockRate": clock_rate})
    reader.handle_rtcp(
        SimpleNamespace(packets=[SR(ssrc=1, ntp=report_time, ts=report_counter)])
    )
    packet = SimpleNamespace(ts=packet_counter)
    actual = reader.absolute_timestamp_from_packet(packet)
    assert isinstance(actual, float)
    assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-6)
    assert reader.relative_timestamp_from_packet(packet) == packet_counter / clock_rate


def test_absolute_timestamp_before_sender_report(reader):
    with pytest.raises(_UnknownClockoffsetError):
        reader.absolute_timestamp_from_packet(SimpleNamespace(ts=232))


def test_sender_report_refresh_and_out_of_order_packets(reader):
    independent = _WallclockRTSPReader("rtsp://example.invalid/other")
    reports = [
        SR(ssrc=1, ntp=1793794350.950418, ts=4294799520),
        # Include a clock correction so ignoring the new report is detectable.
        SR(ssrc=1, ntp=1793794353.8171735, ts=232),
    ]
    for correction, report in enumerate(reports):
        reader.handle_rtcp(SimpleNamespace(packets=[report]))
        for counter, expected in [
            (232, 1793794352.8171735),
            (4294799520, 1793794350.950418),
        ] * 2:
            actual = reader.absolute_timestamp_from_packet(SimpleNamespace(ts=counter))
            assert math.isclose(
                actual, expected + correction, rel_tol=0.0, abs_tol=1e-6
            )
        assert reader.absolute_timestamp_from_packet(report) == report.ntp

    with pytest.raises(_UnknownClockoffsetError):
        independent.absolute_timestamp_from_packet(SimpleNamespace(ts=232))
