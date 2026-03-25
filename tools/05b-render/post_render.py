#!/usr/bin/env python3
"""
Post-render verification pipeline stage.

Runs automatically after successful render to validate caption fidelity.
Never blocks rendering - failures are logged but don't affect render exit.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def run_post_render_verification(
    project_root: Path,
    verbose: bool = False,
    enable_vision: bool = True,
    vision_model: str = "qwen3-vl:32b",
    max_vision_frames: int = 50
) -> Dict[str, Any]:
    """
    Run verification after successful render.
    
    Returns verification results without raising exceptions.
    """
    try:
        from verify_captions import run_verification
        
        project_path = project_root / 'data' / 'project.json'
        data_dir = project_root / 'data'
        
        result = run_verification(
            project_path,
            data_dir,
            extract_frames=True,
            enable_vision=enable_vision,
            vision_model=vision_model,
            max_vision_frames=max_vision_frames,
            verbose=verbose
        )
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'exit_code': 3
        }


def print_verification_summary(result: Dict[str, Any]) -> None:
    """Print concise terminal summary."""
    print("\n" + "=" * 50)
    print("POST RENDER VERIFICATION SUMMARY")
    print("=" * 50)
    
    if not result.get('success'):
        print(f"\nVerification execution failed: {result.get('error', 'Unknown error')}")
        print("Verification execution failed but render completed successfully.")
        return
    
    summary = result.get('summary', {})
    
    print(f"\nText coverage: {summary.get('text_coverage_percent', 0):.2f}%")
    print(f"Mean timing drift: {summary.get('timing_mean_drift_ms', 0):.1f} ms")
    print(f"Max timing drift: {summary.get('timing_max_drift_ms', 0):.1f} ms")
    
    mismatch = summary.get('first_mismatch_index', -1)
    print(f"First mismatch index: {mismatch if mismatch >= 0 else 'None'}")
    
    drift = summary.get('first_drift_index', -1)
    print(f"First drift index: {drift if drift >= 0 else 'None'}")
    
    # Vision verification summary
    if 'vision_coverage_percent' in summary:
        print(f"\nVisibility coverage: {summary['vision_coverage_percent']:.2f}%")
        print(f"Vision failed frames: {summary.get('vision_failed_frames', 0)}")
        print(f"Vision mean confidence: {summary.get('vision_mean_confidence', 0):.2f}")
    
    exit_code = summary.get('verification_exit_code', 3)
    print(f"\nVerification exit code: {exit_code}")
    
    print()
    if exit_code == 0:
        print("Verification passed.")
    else:
        print("Verification detected fidelity issues.")
        print("See HTML report for inspection.")
    
    if result.get('report_path'):
        print(f"\nReport: {result['report_path']}")


def main():
    """Standalone entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Post-render verification')
    parser.add_argument('--project', '-p', type=str, help='Project root path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--no-vision', action='store_true', help='Skip vision verification')
    parser.add_argument('--vision-model', type=str, default='qwen3-vl:32b', help='Vision model')
    parser.add_argument('--max-vision-frames', type=int, default=200, help='Max frames for vision')
    args = parser.parse_args()
    
    project_root = Path(args.project) if args.project else get_project_root()
    
    result = run_post_render_verification(
        project_root,
        verbose=args.verbose,
        enable_vision=not args.no_vision,
        vision_model=args.vision_model,
        max_vision_frames=args.max_vision_frames
    )
    print_verification_summary(result)
    
    return result.get('summary', {}).get('verification_exit_code', 3)


if __name__ == '__main__':
    sys.exit(main())
