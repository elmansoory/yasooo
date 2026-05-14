"""
Quick video labeling helper
===========================
Cuts a video clip and saves it with a JSON label sidecar,
ready for train_model.py to consume.

Usage examples:
    # Label a full short video (spin clip):
    python label_video.py video.mp4 --label Sit --out data/labeled/sit_001

    # Cut seconds 12-15 from a longer video (triple Lutz):
    python label_video.py program.mp4 --label Lutz_3 --start 12 --end 15 --out data/labeled/lutz3_001

Available labels (from src/models/lstm_classifier.py):
    Jumps : Axel_1 Axel_2 Axel_3 Axel_4
            Lutz_1 Lutz_2 Lutz_3 Lutz_4
            Flip_1 Flip_2 Flip_3 Flip_4
            Loop_1 Loop_2 Loop_3 Loop_4
            Salchow_1 Salchow_2 Salchow_3 Salchow_4
            ToeLoop_1 ToeLoop_2 ToeLoop_3 ToeLoop_4
    Spins : Upright  Sit  Camel  Layback  Combination
    Other : StepSequence  Spiral  None
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from src.models.lstm_classifier import LABEL2IDX


def cut_clip(src: str, out_mp4: str, start: float, end: float):
    """Use ffmpeg to cut a clip (no re-encode for speed)."""
    dur = end - start
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", src,
        "-t", str(dur),
        "-c", "copy",
        out_mp4
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        # Fallback: re-encode with cv2
        try:
            import cv2
            cap = cv2.VideoCapture(src)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(out_mp4, fourcc, fps, (w, h))
            cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
            while cap.get(cv2.CAP_PROP_POS_MSEC) < end * 1000:
                ok, frame = cap.read()
                if not ok: break
                out.write(frame)
            cap.release(); out.release()
        except ImportError:
            print("ffmpeg not found and opencv not available — copy the clip manually.")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video",  help="Source video file")
    parser.add_argument("--label", required=True, help="Movement label")
    parser.add_argument("--start", type=float, default=0.0, help="Start time (s)")
    parser.add_argument("--end",   type=float, default=None, help="End time (s)")
    parser.add_argument("--out",   required=True, help="Output path (no extension)")
    parser.add_argument("--notes", default="", help="Optional notes")
    args = parser.parse_args()

    if args.label not in LABEL2IDX:
        print(f"Unknown label '{args.label}'. Available labels:")
        for l in LABEL2IDX:
            print(f"  {l}")
        sys.exit(1)

    out_dir = Path(args.out).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4  = args.out + ".mp4"
    out_json = args.out + ".json"

    import cv2
    cap = cv2.VideoCapture(args.video)
    total_dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 30)
    cap.release()
    end = args.end if args.end is not None else total_dur

    print(f"Cutting {args.video}  [{args.start:.1f}s – {end:.1f}s]  →  {out_mp4}")
    cut_clip(args.video, out_mp4, args.start, end)

    meta = {
        "label":    args.label,
        "source":   args.video,
        "start":    args.start,
        "end":      end,
        "duration": end - args.start,
        "notes":    args.notes,
    }
    Path(out_json).write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"Label saved  →  {out_json}")
    print(f"\nTo train: python train_model.py --data_dir data/labeled")


if __name__ == "__main__":
    main()
