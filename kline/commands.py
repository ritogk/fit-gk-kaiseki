"""High-level commands mapped to confirmed ECM(0x10) IO Control LIDs.

LID/IOCP map confirmed on Honda Fit GK5 RS MT (2014-2020).
See docs/findings.md for the research that produced this table.
"""
from .client import KLineClient


# (LID, IOCP, default_envelope_s, description)
LIDS = {
    "hazard":      (0x08, 0x0F, 15.0, "Hazard lights (envelope ~15s, MICU cancels when doors closed)"),
    "turn_left":   (0x0A, 0x0F, 5.0,  "Left turn signal (envelope ~5s)"),
    "turn_right":  (0x0B, 0x0F, 5.0,  "Right turn signal (envelope ~5s)"),
    "low_beam":    (0x1C, 0x0F, 15.0, "Low beam headlight (envelope ~15s)"),
    "high_beam":   (0x1D, 0x0F, 15.0, "High beam headlight (envelope ~15s)"),
    "fog":         (0x20, 0x0F, 15.0, "Fog lamps (envelope ~15s, requires lights ON to be visible)"),
    "position":    (0x25, 0x0F, 15.0, "Position/parking lights (envelope ~15s)"),
    "lock":        (0x04, 0x01, 0.0,  "Lock all doors (single pulse)"),
    "unlock":      (0x05, 0x01, 0.0,  "Unlock all doors (single pulse)"),
    "trunk":       (0x09, 0x01, 0.0,  "Open trunk (single pulse)"),
    "chirp":       (0x11, 0x01, 0.0,  "Buzzer/chirp tone"),
    "horn":        (0x26, 0x01, 1.0,  "Horn (envelope ~1s, can be shortened with StopDiag)"),
}


def list_commands():
    return {name: {"lid": lid, "iocp": iocp,
                   "default_duration_s": dur, "description": desc}
            for name, (lid, iocp, dur, desc) in LIDS.items()}


def fire(name, duration_s=None):
    if name not in LIDS:
        raise ValueError(f"unknown command: {name}")
    lid, iocp, default_dur, _ = LIDS[name]
    dur = default_dur if duration_s is None else float(duration_s)
    with KLineClient() as cli:
        if iocp == 0x01 or dur <= 0.0:
            return cli.io_control(lid, iocp)
        return cli.fire_envelope(lid, iocp, dur)
