# -*- coding: utf-8 -*-
"""CLI srtclean: bersihkan file SRT, tulis hasil + laporan statistik."""
import argparse
import json
import os
import sys

from .clean import clean_all
from .parser import parse_srt, render_srt
from . import __version__

VERSION = __version__


def read_input(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8"), "utf-8-sig"
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("cp1252"), "cp1252"


def build_parser():
    p = argparse.ArgumentParser(
        prog="srtclean",
        description="Bersihkan file subtitle SRT (tag, deskripsi non-dialog, "
                    "label pembicara, duplikat, waktu tumpang tindih).")
    p.add_argument("input", help="file SRT masukan")
    p.add_argument("-o", "--output", help="file keluaran (default: <nama>.clean.srt)")
    p.add_argument("--in-place", action="store_true",
                   help="tulis kembali ke file masukan")
    p.add_argument("--dry-run", action="store_true",
                   help="hanya tampilkan laporan, tanpa menulis file")
    p.add_argument("--report", action="store_true",
                   help="tampilkan statistik lengkap (JSON) di stdout")
    p.add_argument("--keep-tags", action="store_true", help="jangan buang tag HTML/ASS")
    p.add_argument("--keep-brackets", action="store_true",
                   help="jangan buang [deskripsi] dan baris (...)")
    p.add_argument("--keep-labels", action="store_true",
                   help="jangan buang label pembicara")
    p.add_argument("--no-dedup", action="store_true",
                   help="jangan gabung cue duplikat berurutan")
    p.add_argument("--no-timing", action="store_true",
                   help="jangan perbaiki waktu")
    p.add_argument("--version", action="version", version="%(prog)s " + VERSION)
    return p


def summary_line(stats):
    return ("Cue: %(in)d -> %(out)d (kosong dibuang: %(empty)d, digabung: %(merged)d, "
            "waktu diperbaiki: %(timing)d, tag HTML: %(tags)d, deskripsi [...]: %(brackets)d, "
            "baris (...): %(paren_lines)d, label pembicara: %(labels)d)" % stats)


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.in_place and args.output:
        print("srtclean: --in-place tidak bisa dipakai bersama -o", file=sys.stderr)
        return 2
    try:
        text, enc = read_input(args.input)
    except OSError as e:
        print("srtclean: tidak bisa membaca %s: %s" % (args.input, e.strerror or e),
              file=sys.stderr)
        return 2
    try:
        cues = parse_srt(text)
    except ValueError as e:
        print("srtclean: %s: %s" % (args.input, e), file=sys.stderr)
        return 2
    opts = {"keep_tags": args.keep_tags, "keep_brackets": args.keep_brackets,
            "keep_labels": args.keep_labels, "no_dedup": args.no_dedup,
            "no_timing": args.no_timing}
    cleaned, stats = clean_all(cues, opts)
    stats["encoding"] = enc
    if args.dry_run:
        print(summary_line(stats))
        if args.report:
            print(json.dumps(stats, indent=2, sort_keys=True))
        return 0
    if args.in_place:
        out_path = args.input
    elif args.output:
        out_path = args.output
    else:
        base, _ = os.path.splitext(args.input)
        out_path = base + ".clean.srt"
    try:
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(render_srt(cleaned))
    except OSError as e:
        print("srtclean: tidak bisa menulis %s: %s" % (out_path, e.strerror or e),
              file=sys.stderr)
        return 2
    print(summary_line(stats), file=sys.stderr)
    if args.report:
        print(json.dumps(stats, indent=2, sort_keys=True))
    return 0


def entry():
    sys.exit(main())
