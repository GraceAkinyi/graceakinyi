#!/usr/bin/env python3
"""Transcribe a video/audio file with Whisper (faster-whisper), word-level timestamps.

Usage: transcribe.py <media> <out.json> [model=small] [language]
Writes <out.json> (segments + words with start/end seconds) and a readable
<out>.txt next to it, plus a list of pauses longer than 0.5 s.
"""
import json
import sys
from pathlib import Path

from faster_whisper import WhisperModel


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    media, out = sys.argv[1], Path(sys.argv[2])
    model_name = sys.argv[3] if len(sys.argv) > 3 else "small"
    language = sys.argv[4] if len(sys.argv) > 4 else None

    model = WhisperModel(model_name, device="auto", compute_type="int8")
    segments, info = model.transcribe(media, word_timestamps=True, language=language, vad_filter=False)

    data = {"language": info.language, "duration": info.duration, "segments": [], "words": []}
    for seg in segments:
        words = [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3),
                  "prob": round(w.probability, 3)} for w in (seg.words or [])]
        data["segments"].append({"start": round(seg.start, 3), "end": round(seg.end, 3),
                                 "text": seg.text.strip(), "words": words})
        data["words"].extend(words)

    w = data["words"]
    data["pauses_over_0_5s"] = [
        {"after_word": i, "start": w[i]["end"], "end": w[i + 1]["start"],
         "length": round(w[i + 1]["start"] - w[i]["end"], 3)}
        for i in range(len(w) - 1) if w[i + 1]["start"] - w[i]["end"] > 0.5
    ]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2))
    lines = [f"[{s['start']:7.2f} - {s['end']:7.2f}] {s['text']}" for s in data["segments"]]
    lines.append(f"\n{len(data['pauses_over_0_5s'])} pauses > 0.5 s")
    out.with_suffix(".txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
