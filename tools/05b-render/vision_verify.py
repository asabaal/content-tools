#!/usr/bin/env python3
"""
Vision-based caption verification using Ollama.

Validates that captions actually appear in rendered video frames.
"""

import base64
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import urllib.request
import urllib.error


OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_VISION_MODEL = "qwen3-vl:32b"
DEFAULT_CONFIDENCE_THRESHOLD = 0.75
DEFAULT_MAX_FRAMES = 200
DEFAULT_TIMEOUT = 120  # seconds - vision models need time to load


def check_ollama_available() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/tags",
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception:
        return False


def get_available_vision_models() -> List[str]:
    """Get list of available vision models from Ollama."""
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/tags",
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = data.get('models', [])
            # Vision models typically have 'vl' or 'vision' in name
            vision_models = []
            for m in models:
                name = m.get('name', '').lower()
                if 'vl' in name or 'vision' in name or 'llava' in name or 'moondream' in name:
                    vision_models.append(m.get('name'))
            return vision_models
    except Exception:
        return []


def analyze_frame_with_ollama(
    frame_path: Path,
    expected_text: str,
    model: str = DEFAULT_VISION_MODEL,
    timeout: int = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """
    Send frame to Ollama for vision analysis.
    
    Returns dict with:
    - visible: bool
    - confidence: float
    - notes: str
    - raw_response: str
    """
    if not frame_path.exists():
        return {
            'visible': False,
            'confidence': 0.0,
            'notes': f'Frame not found: {frame_path}',
            'raw_response': None
        }
    
    # Read and encode image
    try:
        with open(frame_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        return {
            'visible': False,
            'confidence': 0.0,
            'notes': f'Failed to read frame: {e}',
            'raw_response': None
        }
    
    # Build prompt
    prompt = f"""You are verifying video caption rendering.

Expected caption text:
"{expected_text}"

Does this text appear visibly in the image?

Answer only in JSON format:
{{
  "visible": true or false,
  "confidence": 0.0 to 1.0,
  "notes": "short explanation"
}}"""
    
    # Build request
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_data],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 200
        }
    }
    
    try:
        req = urllib.request.Request(
            OLLAMA_API_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result = json.loads(response.read().decode('utf-8'))
            response_text = result.get('response', '')
            
            # Parse JSON from response
            # Model might include extra text, try to extract JSON
            try:
                # Find JSON object in response
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response_text[start:end]
                    parsed = json.loads(json_str)
                    return {
                        'visible': parsed.get('visible', False),
                        'confidence': float(parsed.get('confidence', 0.0)),
                        'notes': parsed.get('notes', ''),
                        'raw_response': response_text
                    }
            except json.JSONDecodeError:
                pass
            
            # Fallback: try to parse visible from text
            visible = 'visible": true' in response_text.lower() or '"visible":true' in response_text.lower()
            
            return {
                'visible': visible,
                'confidence': 0.5 if visible else 0.3,
                'notes': 'Parsed from non-JSON response',
                'raw_response': response_text
            }
            
    except urllib.error.URLError as e:
        return {
            'visible': False,
            'confidence': 0.0,
            'notes': f'Ollama connection error: {e}',
            'raw_response': None
        }
    except Exception as e:
        return {
            'visible': False,
            'confidence': 0.0,
            'notes': f'Vision analysis error: {e}',
            'raw_response': None
        }


def run_vision_verification(
    frames_dir: Path,
    caption_events: List[Dict],
    frames: List[Dict],
    model: str = DEFAULT_VISION_MODEL,
    max_frames: int = DEFAULT_MAX_FRAMES,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run vision verification on extracted frames.
    
    Args:
        frames_dir: Directory containing extracted frames (verification/frames)
        caption_events: List of caption events
        frames: List of frame info dicts from extract_verification_frames
        model: Ollama vision model to use
        max_frames: Maximum frames to analyze
        confidence_threshold: Minimum confidence to consider visible
        verbose: Print progress
    
    Returns:
        Dict with vision verification results
    """
    # Check Ollama availability
    if not check_ollama_available():
        return {
            'success': False,
            'error': 'Ollama not available',
            'skipped': True,
            'results': []
        }
    
    # Get available vision models
    available_models = get_available_vision_models()
    if available_models and model not in available_models:
        # Use first available vision model
        model = available_models[0]
        if verbose:
            print(f"Using available vision model: {model}")
    
    # Limit frames
    frames_to_analyze = frames[:max_frames]
    
    results = []
    visible_count = 0
    total_confidence = 0.0
    first_failed_index = -1
    
    for i, frame_info in enumerate(frames_to_analyze):
        frame_rel_path = frame_info.get('frame_path')
        
        # Handle path - frame_path might be relative to verification dir
        # so frames_dir might already be verification/frames
        if frame_rel_path:
            # If path starts with 'frames/', we need to go up one level
            if frame_rel_path.startswith('frames/'):
                frame_path = frames_dir.parent / frame_rel_path
            else:
                frame_path = frames_dir / Path(frame_rel_path).name
        else:
            frame_path = None
        
        if not frame_path or not frame_path.exists():
            results.append({
                'frame_index': i,
                'caption_index': frame_info.get('event_index'),
                'timestamp': frame_info.get('output_time'),
                'expected_text': frame_info.get('event_text', ''),
                'visible': False,
                'confidence': 0.0,
                'notes': 'Frame not found',
                'status': 'missing'
            })
            continue
        
        expected_text = frame_info.get('event_text', '')
        
        if verbose:
            print(f"  Analyzing frame {i+1}/{len(frames_to_analyze)}: {expected_text[:30]}...")
        
        analysis = analyze_frame_with_ollama(
            frame_path,
            expected_text,
            model=model
        )
        
        # Determine status
        visible = analysis.get('visible', False)
        confidence = analysis.get('confidence', 0.0)
        
        if visible and confidence >= confidence_threshold:
            status = 'visible'
            visible_count += 1
        elif visible:
            status = 'low_confidence'
        else:
            status = 'invisible'
        
        if (not visible or confidence < confidence_threshold) and first_failed_index < 0:
            first_failed_index = i
        
        total_confidence += confidence
        
        results.append({
            'frame_index': i,
            'caption_index': frame_info.get('event_index'),
            'timestamp': frame_info.get('output_time'),
            'expected_text': expected_text,
            'expected_first_word': frame_info.get('expected_first_word'),
            'visible': visible,
            'confidence': confidence,
            'notes': analysis.get('notes', ''),
            'status': status,
            'frame_path': str(frame_path.relative_to(frames_dir.parent.parent)) if frame_path else None
        })
    
    # Calculate metrics
    total_frames = len(frames_to_analyze)
    visibility_coverage = (visible_count / total_frames * 100) if total_frames > 0 else 0.0
    mean_confidence = (total_confidence / total_frames) if total_frames > 0 else 0.0
    failed_frames = total_frames - visible_count
    
    return {
        'success': True,
        'skipped': False,
        'model': model,
        'total_frames': total_frames,
        'visible_frames': visible_count,
        'failed_frames': failed_frames,
        'visibility_coverage_percent': round(visibility_coverage, 2),
        'mean_confidence': round(mean_confidence, 2),
        'first_failed_index': first_failed_index if first_failed_index >= 0 else None,
        'confidence_threshold': confidence_threshold,
        'results': results
    }


def print_vision_summary(vision_result: Dict[str, Any]) -> None:
    """Print vision verification summary to terminal."""
    if vision_result.get('skipped'):
        print("\nVision verification skipped:", vision_result.get('error', 'Unknown reason'))
        return
    
    if not vision_result.get('success'):
        print("\nVision verification failed:", vision_result.get('error', 'Unknown error'))
        return
    
    print("\n" + "=" * 50)
    print("VISION CAPTION VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"\nVisibility coverage: {vision_result['visibility_coverage_percent']:.2f}%")
    print(f"Visible frames: {vision_result['visible_frames']}/{vision_result['total_frames']}")
    print(f"Failed frames: {vision_result['failed_frames']}")
    print(f"Mean confidence: {vision_result['mean_confidence']:.2f}")
    
    if vision_result.get('first_failed_index') is not None:
        print(f"First failed frame: {vision_result['first_failed_index']}")
    
    print(f"\nModel used: {vision_result.get('model', 'unknown')}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Vision-based caption verification')
    parser.add_argument('--frames-dir', '-f', type=str, required=True, help='Frames directory')
    parser.add_argument('--model', '-m', type=str, default=DEFAULT_VISION_MODEL, help='Vision model')
    parser.add_argument('--max-frames', type=int, default=DEFAULT_MAX_FRAMES, help='Max frames to analyze')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    frames_dir = Path(args.frames_dir)
    
    if not check_ollama_available():
        print("Error: Ollama not available")
        sys.exit(1)
    
    # Get list of frames
    frame_files = sorted(frames_dir.glob('frame_*.png'))
    
    if not frame_files:
        print("No frames found")
        sys.exit(1)
    
    print(f"Found {len(frame_files)} frames")
    
    # Run verification with mock frame info
    frames_info = []
    for i, fp in enumerate(frame_files[:args.max_frames]):
        # Parse timestamp from filename
        import re
        match = re.search(r'(\d+\.\d+)s', fp.name)
        timestamp = float(match.group(1)) if match else i * 3.0
        
        frames_info.append({
            'event_index': i,
            'output_time': timestamp,
            'event_text': f'Caption {i}',
            'frame_path': fp.name
        })
    
    result = run_vision_verification(
        frames_dir,
        [],
        frames_info,
        model=args.model,
        max_frames=args.max_frames,
        verbose=args.verbose
    )
    
    print_vision_summary(result)
    
    # Save results
    output_path = frames_dir.parent / 'vision_summary.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
