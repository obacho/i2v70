#!/usr/bin/env python3
import subprocess
import os
import sys
import shutil

# -----------------------------
# USER CONFIGURATION
# -----------------------------
# Configuration for each project
CONFIGS = {
    "päda": {
        "image": "päda.jpg",
        "width": 692,
        "height": 1032,
        "timeline": [
            ("still", 10),
            ("clip", "päda_stroke.mp4"),
            ("still", 20),
            ("clip", "päda_v.mp4"),
            ("still", 5),
            ("clip", "päda_zunge.mp4"),
            ("still", 15),
        ],
        "use_first_frame": True,
        "use_next_video_frame": True,
        "use_last_video_frame": False,
        "output": "päda_ff_final.mp4",
    },
    "opa": {
        "image": "opa.jpg",
        "width": 620,
        "height": 760,
        "timeline": [
            ("still", 5),
            ("clip", "opa1.MP4"),
            ("clip", "opa2.MP4"),
            ("clip", "opa3.MP4"),
        ],
        "use_first_frame": True,
        "use_next_video_frame": True,
        "use_last_video_frame": False,
        "output": "opa_ff_final.mp4",
    },
    "opa_singlemove": {
        "image": "opa.jpg",
        "width": 620,
        "height": 760,
        "timeline": [
            ("still", 5),
            ("clip", "opa1.mp4"),
            ("still", 5),            
        ],
        "use_first_frame": False,
        "use_next_video_frame": False,
        "use_last_video_frame": True,
        "output": "opa_singlemove.mp4",
    },    
    "braut": {
        "image": "braut.jpg",
        "width": 890,
        "height": 1244,
        "timeline": [
            ("still", 5),
            ("clip", "braut_winkt.mp4"),
            ("still", 10),
            ("clip", "braut_kiss.mp4"),
            ("still", 15),
        ],
        "use_first_frame": False,
        "use_next_video_frame": False,
        "use_last_video_frame": False,
        "output": "braut_final.mp4",
    },
    "omifamilie": {
        "image": "omifamilie.jpg",
        "width": 1024,
        "height": 854,
        "timeline": [
            ("still", 5),
            ("clip", "omifamilie_wave.mp4"),
            ("clip", "omifamilie_wave_reversed.mp4"),            
            ("still", 15),
        ],
        "use_first_frame": True,
        "use_next_video_frame": False,
        "use_last_video_frame": False,
        "output": "omifamilie_final.mp4",
    },    
    "parkbank": {
        "image": "parkbank.jpg",
        "width": 1100,
        "height": 936,
        "timeline": [
            ("still", 5),
            ("clip", "parkbank_bike.mp4"),
            ("still", 3),
            ("clip", "parkbank_nosedigger.mp4"),
            ("still", 3),
            ("clip", "parkbank_renate_leaves.mp4"),
            ("still", 3),
            ("clip", "parkbank_legs.mp4"),
            ("still", 5),
        ],
        "use_first_frame": True,
        "use_next_video_frame": True,
        "use_last_video_frame": False,
        "output": "parkbank_final.mp4",
    },     
}

# Select which config to use
ACTIVE_CONFIG = "omifamilie"

# Apply the selected configuration
config = CONFIGS[ACTIVE_CONFIG]
IMAGE = config["image"]
image_width = config["width"]
image_height = config["height"]
TIMELINE = config["timeline"]
USE_FIRST_FRAME = config["use_first_frame"]
USE_NEXT_VIDEO_FRAME = config["use_next_video_frame"]
USE_LAST_VIDEO_FRAME = config["use_last_video_frame"]
OUTPUT = config["output"]

FPS = 30
RESOLUTION = f"{image_width}:{image_height}"
WORKDIR = "_work"

# -----------------------------
# HELPERS
# -----------------------------
def run(cmd):
    print("▶", " ".join(cmd))
    # Add -loglevel error to ffmpeg commands to reduce verbosity
    if cmd[0] == "ffmpeg":
        cmd.insert(1, "-loglevel")
        cmd.insert(2, "error")
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
    
def get_next_video(index):
    """Find the next video clip after the given index in the timeline"""
    for i in range(index + 1, len(TIMELINE)):
        kind, value = TIMELINE[i]
        if kind == "clip":
            return value
    return None    

def get_previous_video(index):
    """Find the previous video clip before the given index in the timeline"""
    for i in range(index - 1, -1, -1):
        kind, value = TIMELINE[i]
        if kind == "clip":
            return value
    return None

def extract_first_frame(video_path, output_name):
    """Extract first frame from a video"""
    run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"scale={RESOLUTION}:force_original_aspect_ratio=increase,crop={RESOLUTION}",
        "-frames:v", "1",
        output_name
    ])

def extract_last_frame(video_path, output_name):
    """Extract last frame from a video"""
    run([
        "ffmpeg", "-y",
        "-sseof", "-0.1",  # Seek to 0.1 seconds before end
        "-i", video_path,
        "-vf", f"scale={RESOLUTION}:force_original_aspect_ratio=increase,crop={RESOLUTION}",
        "-frames:v", "1",
        output_name
    ])

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
# DETERMINE SOURCE IMAGE (for master still if not using next/last video frames)
# -----------------------------
if not USE_NEXT_VIDEO_FRAME and not USE_LAST_VIDEO_FRAME:
    if USE_FIRST_FRAME:
        first_video = get_first_video()
        if not first_video:
            print("ERROR: No video clips found in TIMELINE", file=sys.stderr)
            sys.exit(1)
        
        print(f"📸 Extracting first frame from {first_video}")
        source_image = "first_frame.jpg"
        extract_first_frame(os.path.join("..", first_video), source_image)
    else:
        source_image = os.path.join("..", IMAGE)

    # -----------------------------
    # CREATE STILL MASTER VIDEO (old method)
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

for idx, (kind, value) in enumerate(TIMELINE):
    if kind == "still":
        out = f"still_{still_index}.mp4"
        
        if USE_NEXT_VIDEO_FRAME:
            # Find the next video in the timeline
            next_video = get_next_video(idx)
            
            if next_video:
                print(f"🖼️  Creating still from next video: {next_video}")
                # Extract first frame from next video
                frame_img = f"frame_still_{still_index}.jpg"
                extract_first_frame(os.path.join("..", next_video), frame_img)
                
                # Create still video from that frame
                run([
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", frame_img,
                    "-t", str(value),
                    "-r", str(FPS),
                    "-pix_fmt", "yuv420p",
                    out
                ])
            else:
                # No next video found, use fallback
                print(f"⚠️  No next video found for still {still_index}, using fallback")
                if USE_FIRST_FRAME:
                    first_video = get_first_video()
                    frame_img = f"frame_still_{still_index}.jpg"
                    extract_first_frame(os.path.join("..", first_video), frame_img)
                    source = frame_img
                else:
                    source = os.path.join("..", IMAGE)
                
                run([
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", source,
                    "-t", str(value),
                    "-r", str(FPS),
                    "-vf", f"scale={RESOLUTION}",
                    "-pix_fmt", "yuv420p",
                    out
                ])
        
        elif USE_LAST_VIDEO_FRAME:
            # Find the previous video in the timeline
            prev_video = get_previous_video(idx)
            
            if prev_video:
                print(f"🖼️  Creating still from last frame of previous video: {prev_video}")
                # Extract last frame from previous video
                frame_img = f"frame_still_{still_index}.jpg"
                extract_last_frame(os.path.join("..", prev_video), frame_img)
                
                # Create still video from that frame
                run([
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", frame_img,
                    "-t", str(value),
                    "-r", str(FPS),
                    "-pix_fmt", "yuv420p",
                    out
                ])
            else:
                # No previous video found, use fallback
                print(f"⚠️  No previous video found for still {still_index}, using fallback")
                if USE_FIRST_FRAME:
                    first_video = get_first_video()
                    frame_img = f"frame_still_{still_index}.jpg"
                    extract_first_frame(os.path.join("..", first_video), frame_img)
                    source = frame_img
                else:
                    source = os.path.join("..", IMAGE)
                
                run([
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", source,
                    "-t", str(value),
                    "-r", str(FPS),
                    "-vf", f"scale={RESOLUTION}",
                    "-pix_fmt", "yuv420p",
                    out
                ])
        
        else:
            # Old method: use master still
            run([
                "ffmpeg", "-y",
                "-i", "still_master.mp4",
                "-ss", str(still_offset),
                "-t", str(value),
                out
            ])
            still_offset += value
        
        concat_entries.append(out)
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
