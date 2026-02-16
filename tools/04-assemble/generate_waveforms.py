#!/usr/bin/env python3
"""
Generate waveform data for audio visualization.

Reads video_combined.mp4 to generate waveform peak data for the entire video.

Usage:
    python tools/04-assemble/generate_waveforms.py

Output:
    data/waveforms.json

Requires: ffmpeg (for audio extraction)
"""

import json
import os
import subprocess
import sys
import wave
import struct
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VIDEO_PATH = DATA_DIR / "video_combined.mp4"
OUTPUT_PATH = DATA_DIR / "waveforms.json"
TEMP_AUDIO_PATH = DATA_DIR / ".temp_audio.wav"

PEAKS_PER_SECOND = 100


def extract_audio():
    """Extract audio from video file as WAV using ffmpeg."""
    print(f"Extracting audio from {VIDEO_PATH}...")
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(VIDEO_PATH),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "1",
        str(TEMP_AUDIO_PATH)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr}")
        raise RuntimeError("Failed to extract audio")
    
    print("Audio extracted successfully.")


def read_full_audio_peaks(audio_path, sample_rate=44100):
    """Read entire audio file and generate peaks."""
    with wave.open(str(audio_path), 'rb') as wav:
        sampwidth = wav.getsampwidth()
        framerate = wav.getframerate()
        n_frames = wav.getnframes()
        duration = n_frames / framerate
        
        print(f"Audio duration: {duration:.2f}s")
        print(f"Reading {n_frames} frames...")
        
        raw_data = wav.readframes(n_frames)
        
        if sampwidth == 2:
            fmt = f'<{len(raw_data)//2}h'
            samples = struct.unpack(fmt, raw_data)
        else:
            samples = [0] * (len(raw_data) // sampwidth)
        
        num_peaks = int(duration * PEAKS_PER_SECOND)
        samples_per_peak = max(1, len(samples) // num_peaks)
        
        print(f"Generating {num_peaks} peaks...")
        
        peaks = []
        for i in range(num_peaks):
            start = i * samples_per_peak
            end = min(start + samples_per_peak, len(samples))
            chunk = samples[start:end]
            if chunk:
                peak = max(abs(s) for s in chunk) / 32768.0
                peaks.append(round(peak, 4))
            else:
                peaks.append(0)
            
            if (i + 1) % 5000 == 0:
                print(f"  Processed {i + 1}/{num_peaks} peaks")
        
        return peaks, duration


def generate_waveforms():
    """Generate waveform data for entire video."""
    
    if not VIDEO_PATH.exists():
        print(f"Error: {VIDEO_PATH} not found")
        sys.exit(1)
    
    extract_audio()
    
    peaks, duration = read_full_audio_peaks(TEMP_AUDIO_PATH)
    
    output = {
        'video_id': 'combined',
        'sample_rate': 44100,
        'peaks_per_second': PEAKS_PER_SECOND,
        'duration': round(duration, 3),
        'peaks': peaks,
        'total_peaks': len(peaks)
    }
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)
    
    if TEMP_AUDIO_PATH.exists():
        os.remove(TEMP_AUDIO_PATH)
    
    print(f"Waveform data saved to {OUTPUT_PATH}")
    print(f"Total peaks: {len(peaks)}")
    print(f"Duration: {duration:.2f}s")


if __name__ == '__main__':
    generate_waveforms()
