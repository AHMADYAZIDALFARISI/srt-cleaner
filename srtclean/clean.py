# -*- coding: utf-8 -*-
"""Langkah pembersihan SRT. Semua langkah bisa dimatikan lewat opsi CLI.

Aturan yang dipakai (didokumentasikan di README):
- Tag HTML (<i>, <font ...>) dan tag gaya ASS ({...}) dibuang; entitas
  HTML (&amp; dsb.) diurai.
- Segmen [dalam kurung siku] dibuang: menurut konvensi subtitle itu
  deskripsi non-dialog (bunyi, musik, keterangan suasana).
- Baris yang SELURUHNYA dalam (tanda kurung) dibuang dengan alasan sama.
  Tanda kurung di tengah kalimat dialog dipertahankan.
- Label pembicara di awal baris ("BUDI: Halo") dibuang bila prefiksnya
  huruf kapital/angka (min. 2 karakter). "Halo: apa kabar" tidak dibuang
  karena bukan label.
- Cue yang teksnya kosong setelah dibersihkan dibuang.
- Cue berurutan dengan teks persis sama digabung (ujung = ujung terjauh).
- Waktu diperbaiki: diurutkan, durasi <= 0 jadi 1000 ms, tumpang tindih
  dipangkas dari cue sebelumnya (geser kecil bila perlu, min. 200 ms).
"""
import html as htmlmod
import re

from .parser import Cue

HTML_TAG_RE = re.compile(r"<[^>]+>")
ASS_TAG_RE = re.compile(r"\{[^}]*\}")
BRACKET_RE = re.compile(r"\[[^\]\[]*\]")
LABEL_RE = re.compile(r"^([A-Z0-9][A-Z0-9 .'\-]{1,19}):\s+")
WS_RE = re.compile(r"\s+")

STAT_KEYS = ("tags", "brackets", "paren_lines", "labels",
             "empty", "merged", "timing")


def _clean_line(line, stats, opts):
    if not opts.get("keep_tags"):
        n = len(HTML_TAG_RE.findall(line)) + len(ASS_TAG_RE.findall(line))
        line = HTML_TAG_RE.sub("", line)
        line = ASS_TAG_RE.sub("", line)
        stats["tags"] += n
        line = htmlmod.unescape(line)
    if not opts.get("keep_brackets"):
        n = len(BRACKET_RE.findall(line))
        line = BRACKET_RE.sub("", line)
        stats["brackets"] += n
    return WS_RE.sub(" ", line).strip()


def _strip_label(line, stats, opts):
    if opts.get("keep_labels"):
        return line
    m = LABEL_RE.match(line)
    if m:
        stats["labels"] += 1
        return line[m.end():].strip()
    return line


def clean_cue(cue, stats, opts):
    out_lines = []
    for line in cue.lines:
        line = _clean_line(line, stats, opts)
        if not line:
            continue
        if not opts.get("keep_brackets") and line.startswith("(") and line.endswith(")"):
            stats["paren_lines"] += 1
            continue
        line = _strip_label(line, stats, opts)
        if line:
            out_lines.append(line)
    if not out_lines:
        return None
    return Cue(start=cue.start, end=cue.end, lines=out_lines)


def dedup(cues, stats):
    out = []
    for c in cues:
        if out and "\n".join(out[-1].lines) == "\n".join(c.lines):
            out[-1].end = max(out[-1].end, c.end)
            stats["merged"] += 1
        else:
            out.append(c)
    return out


def fix_timing(cues, stats):
    cues = sorted(cues, key=lambda c: c.start)
    for i, c in enumerate(cues):
        if c.end <= c.start:
            c.end = c.start + 1000
            stats["timing"] += 1
        if i and c.start < cues[i - 1].end:
            prev = cues[i - 1]
            prev.end = c.start
            stats["timing"] += 1
            if prev.end <= prev.start:
                prev.end = prev.start + 200
                c.start = prev.end + 1
                if c.end <= c.start:
                    c.end = c.start + 1000
    return cues


def clean_all(cues, opts=None):
    opts = opts or {}
    stats = {k: 0 for k in STAT_KEYS}
    stats["in"] = len(cues)
    kept = []
    for c in cues:
        nc = clean_cue(c, stats, opts)
        if nc is None:
            stats["empty"] += 1
        else:
            kept.append(nc)
    if not opts.get("no_dedup"):
        kept = dedup(kept, stats)
    if not opts.get("no_timing"):
        kept = fix_timing(kept, stats)
    stats["out"] = len(kept)
    return kept, stats
