#!/usr/bin/env python3
"""
Generate waveform data for audio visualization.

Reads video_combined.mp4 and transcript_combined.json to generate
waveform peak data for each segment.

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
TRANSCRIPT_PATH = DATA_DIR / "transcript_combined.json"
OUTPUT_PATH = DATA_DIR / "waveforms.json"
TEMP_AUDIO_PATH = DATA_DIR / ".temp_audio.wav"

PEAKS_PER_SECOND = 50


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


def read_audio_peaks(audio_path, start_time, end_time, sample_rate=44100):
    """Read audio data and generate peaks for a time range."""
    with wave.open(str(audio_path), 'rb') as wav:
        n_channels = wav.getnchannels()
        sampwidth = wav.getsampwidth()
        framerate = wav.getframerate()
        n_frames = wav.getnframes()
        
        start_frame = int(start_time * framerate)
        end_frame = int(end_time * framerate)
        duration_frames = end_frame - start_frame
        
        if start_frame >= n_frames:
            return [0] * 100
        if end_frame > n_frames:
            end_frame = n_frames
            duration_frames = end_frame - start_frame
        
        wav.setpos(start_frame)
        frames_to_read = end_frame - start_frame
        raw_data = wav.readframes(frames_to_read)
        
        if sampwidth == 2:
            fmt = f'<{len(raw_data)//2}h'
            samples = struct.unpack(fmt, raw_data)
        else:
            samples = [0] * (len(raw_data) // sampwidth)
        
        duration = end_time - start_time
        num_peaks = max(1, int(duration * PEAKS_PER_SECOND))
        samples_per_peak = max(1, len(samples) // num_peaks)
        
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
        
        return peaks


def generate_waveforms():
    """Generate waveform data for all segments in transcript."""
    
    if not TRANSCRIPT_PATH.exists():
        print(f"Error: {TRANSCRIPT_PATH} not found")
        print("Run the transcribe tool first.")
        sys.exit(1)
    
    with open(TRANSCRIPT_PATH, 'r') as f:
        transcript = json.load(f)
    
    segments = transcript.get('segments', [])
    if not segments:
        print("No segments found in transcript")
        sys.exit(1)
    
    print(f"Found {len(segments)} segments")
    
    extract_audio()
    
    print("Generating waveform peaks...")
    waveform_segments = {}
    
    for i, segment in enumerate(segments):
        seg_id = str(segment.get('id', i))
        start = segment.get('start', 0)
        end = segment.get('end', 0)
        
        if end <= start:
            waveform_segments[seg_id] = {
                'start': start,
                'end': end,
                'peaks': [0] * 100,
                'duration': 0
            }
            continue
        
        peaks = read_audio_peaks(TEMP_AUDIO_PATH, start, end)
        
        waveform_segments[seg_id] = {
            'start': start,
            'end': end,
            'peaks': peaks,
            'duration': round(end - start, 3)
        }
        
        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(segments)} segments")
    
    output = {
        'video_id': 'combined',
        'sample_rate': 44100,
        'peaks_per_second': PEAKS_PER_SECOND,
        'segments': waveform_segments
    }
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)
    
    if TEMP_AUDIO_PATH.exists():
        os.remove(TEMP_AUDIO_PATH)
    
    print(f"Waveform data saved to {OUTPUT_PATH}")
    print(f"Total segments: {len(waveform_segments)}")


if __name__ == '__main__':
    generate_waveforms()
