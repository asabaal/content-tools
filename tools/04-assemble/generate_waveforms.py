#!/usr/bin/env python3
"""
Generate waveform data for audio visualization.

Reads video_combined.mp4 to generate waveform peak data for the entire video.

Usage:
    python tools/04-assemble/generate_waveforms.py
    python tools/04-assemble/generate_waveforms.py --project /path/to/project

Output:
    waveforms.json in project directory

Requires: ffmpeg (for audio extraction)
"""

import argparse
import json
import os
import subprocess
import sys
import wave
import struct
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

PEAKS_PER_SECOND = 100


def get_project_config(project_arg: str | None = None):
    """Load project config from path or use default."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from core.project_config import ProjectConfig
    
    if project_arg:
        project_path = Path(project_arg)
        if project_path.is_file() and project_path.name == 'project.json':
            config_path = project_path
        else:
            config_path = project_path / 'project.json'
        return ProjectConfig.load(config_path)
    else:
        from core.project_config import get_default_project_path
        return ProjectConfig.load(get_default_project_path())


def extract_audio(video_path: Path, temp_audio_path: Path):
    """Extract audio from video file as WAV using ffmpeg."""
    print(f"Extracting audio from {video_path}...")
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "1",
        str(temp_audio_path)
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


def generate_waveforms(config):
    """Generate waveform data for entire video."""
    
    video_path = config.combined_video
    output_path = config.waveforms
    temp_audio_path = config.data_dir / ".temp_audio.wav"
    
    if not video_path.exists():
        print(f"Error: {video_path} not found")
        sys.exit(1)
    
    extract_audio(video_path, temp_audio_path)
    
    peaks, duration = read_full_audio_peaks(temp_audio_path)
    
    output = {
        'video_id': 'combined',
        'sample_rate': 44100,
        'peaks_per_second': PEAKS_PER_SECOND,
        'duration': round(duration, 3),
        'peaks': peaks,
        'total_peaks': len(peaks)
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    if temp_audio_path.exists():
        os.remove(temp_audio_path)
    
    print(f"Waveform data saved to {output_path}")
    print(f"Total peaks: {len(peaks)}")
    print(f"Duration: {duration:.2f}s")


def main():
    parser = argparse.ArgumentParser(description='Generate waveform data for video')
    parser.add_argument('--project', '-p', type=str,
                        default=None,
                        help='Path to project directory (default: data)')
    args = parser.parse_args()
    
    config = get_project_config(args.project)
    print(f"Project: {config.name}")
    print(f"Data directory: {config.data_dir}")
    
    generate_waveforms(config)


if __name__ == '__main__':
    main()
