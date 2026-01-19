#!/usr/bin/env python3
import subprocess
import os
import sys
import shutil

# -----------------------------
# USER CONFIGURATION
# -----------------------------
# Set USE_FIRST_FRAME to True to extract first frame from first video
# Set to False to use IMAGE file instead
USE_FIRST_FRAME = True

# päda
IMAGE = "päda.jpg"
image_width = 692
image_height = 1032
TIMELINE = [
    ("still", 10),
    ("clip", "päda_stroke.mp4"),
    ("still", 20),
    ("clip", "päda_v.mp4"),
    ("still", 5),
    ("clip", "päda_zunge.mp4"),
    ("still", 15),
]
#opa
IMAGE = "opa.jpg"
image_width = 620
image_height = 760
TIMELINE = [
    ("still",  5),
    ("clip", "opa1.MP4"),
#    ("still",  1),
    ("clip", "opa2.MP4"),
#    ("still", 5),
    ("clip", "opa3.MP4"),
#    ("still", 15),
]
OUTPUT = IMAGE.replace('.jpg', '_ff_final.mp4')
USE_FIRST_FRAME = True

#braut
IMAGE = "braut.jpg"
image_width = 890
image_height = 1244 
TIMELINE = [
    ("still",  5),
    ("clip", "braut_winkt.mp4"),
    ("still",  10),
    ("clip", "braut_kiss.mp4"),
    ("still", 15),
]
OUTPUT = IMAGE.replace('.jpg', '_final.mp4')
USE_FIRST_FRAME = False

FPS = 30
RESOLUTION = f"{image_width}:{image_height}"
WORKDIR = "_work"

# -----------------------------
# HELPERS
# -----------------------------
def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

def ensure_ffmpeg():
    if not shutil.which("ffmpeg"):
        print("ffmpeg not found in PATH", file=sys.stderr)
        sys.exit(1)

def get_first_video():
    """Find the first video clip in the timeline"""
    for kind, value in TIMELINE:
        if kind == "clip":
            return value
    return None

# -----------------------------
# MAIN
# -----------------------------
ensure_ffmpeg()
os.makedirs(WORKDIR, exist_ok=True)
os.chdir(WORKDIR)

# Cleanup
for f in os.listdir("."):
    if f.endswith(".mp4") or f.endswith(".jpg") or f == "list.txt":
        os.remove(f)

# -----------------------------
# DETERMINE SOURCE IMAGE
# -----------------------------
if USE_FIRST_FRAME:
    first_video = get_first_video()
    if not first_video:
        print("ERROR: No video clips found in TIMELINE", file=sys.stderr)
        sys.exit(1)
    
    print(f"📸 Extracting first frame from {first_video}")
    source_image = "first_frame.jpg"
    
    # Extract first frame
    run([
        "ffmpeg", "-y",
        "-i", os.path.join("..", first_video),
        "-vf", f"scale={RESOLUTION}:force_original_aspect_ratio=increase,crop={RESOLUTION}",
        "-frames:v", "1",
        source_image
    ])
else:
    source_image = os.path.join("..", IMAGE)

# -----------------------------
# CREATE STILL MASTER VIDEO
# -----------------------------
total_still_duration = sum(
    duration for kind, duration in TIMELINE if kind == "still"
)

run([
    "ffmpeg", "-y",
    "-loop", "1",
    "-i", source_image,
    "-t", str(total_still_duration),
    "-r", str(FPS),
    "-vf", f"scale={RESOLUTION}",
    "-pix_fmt", "yuv420p",
    "still_master.mp4"
])

# -----------------------------
# PROCESS TIMELINE
# -----------------------------
concat_entries = []
still_offset = 0
still_index = 1
clip_index = 1

for kind, value in TIMELINE:
    if kind == "still":
        out = f"still_{still_index}.mp4"
        run([
            "ffmpeg", "-y",
            "-i", "still_master.mp4",
            "-ss", str(still_offset),
            "-t", str(value),
            out
        ])
        concat_entries.append(out)
        still_offset += value
        still_index += 1
    elif kind == "clip":
        out = f"clip_{clip_index}.mp4"
        run([
            "ffmpeg", "-y",
            "-i", os.path.join("..", value),
            "-r", str(FPS),
            # Center crop - change this if you want different crop positioning
            "-vf", f"scale={RESOLUTION}:force_original_aspect_ratio=increase,crop={RESOLUTION}",
            "-pix_fmt", "yuv420p",
            out
        ])
        concat_entries.append(out)
        clip_index += 1
    else:
        raise ValueError(f"Unknown timeline entry: {kind}")

# -----------------------------
# CONCATENATE
# -----------------------------
with open("list.txt", "w") as f:
    for entry in concat_entries:
        f.write(f"file '{entry}'\n")

run([
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", "list.txt",
    "-c", "copy",
    OUTPUT
])

shutil.move(OUTPUT, os.path.join("..", OUTPUT))
print(f"\n✅ Done: {OUTPUT}")
