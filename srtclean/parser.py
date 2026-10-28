# -*- coding: utf-8 -*-
"""Parser SRT yang toleran: BOM, CRLF, nomor cue hilang, koma/titik di milidetik."""
import re
from dataclasses import dataclass, field

TS_RE = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*"
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})"
)


@dataclass
class Cue:
    start: int  # milidetik
    end: int    # milidetik
    lines: list = field(default_factory=list)
    index: int = None


def parse_time(h, m, s, ms):
    ms = int(str(ms).ljust(3, "0"))
    return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + ms


def format_time(total_ms):
    total_ms = max(0, int(total_ms))
    ms = total_ms % 1000
    sec = total_ms // 1000
    return "%02d:%02d:%02d,%03d" % (sec // 3600, (sec // 60) % 60, sec % 60, ms)


def parse_srt(text):
    """Kembalikan list Cue. Blok tanpa baris waktu yang valid -> ValueError."""
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", text.strip("\n"))
    cues = []
    for bi, block in enumerate(blocks, 1):
        lines = block.split("\n")
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        if not lines:
            continue
        idx = None
        if re.fullmatch(r"\d+", lines[0].strip()):
            idx = int(lines[0].strip())
            lines = lines[1:]
            if not lines:
                raise ValueError("blok %d: nomor tanpa baris waktu" % bi)
        m = TS_RE.fullmatch(lines[0].strip())
        if not m:
            raise ValueError("blok %d: baris waktu tidak valid: %r" % (bi, lines[0]))
        g = m.groups()
        cues.append(Cue(start=parse_time(*g[0:4]), end=parse_time(*g[4:8]),
                        lines=lines[1:], index=idx))
    return cues


def render_srt(cues):
    """Render ulang dengan penomoran berurutan dari 1."""
    out = []
    for i, c in enumerate(cues, 1):
        out.append(str(i))
        out.append("%s --> %s" % (format_time(c.start), format_time(c.end)))
        out.extend(c.lines)
        out.append("")
    return "\n".join(out) if out else ""
