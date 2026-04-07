#!/usr/bin/env python3
"""Machine-readable ACE-Step subprocess entry point.

Outputs JSON to stdout. Designed for subprocess.run() invocation.
Called by TCP's music_gen.py via the ACE-Step Python 3.10 environment.
"""
import argparse
import json
import shutil
import sys
import os

sys.path.insert(0, '/mnt/storage/python_env/ace_step_env/lib/python3.10/site-packages')

STUB_PATH = "/mnt/storage/python_env/ace_step_env/lib/python3.10/site-packages/transformers/modeling_layers.py"
if not os.path.exists(STUB_PATH):
    with open(STUB_PATH, 'w') as f:
        f.write("class GradientCheckpointingLayer:\n    pass\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--duration", required=True, type=float)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--guidance", type=float, default=7.0)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--outfile", required=True)
    args = parser.parse_args()

    import torch

    try:
        from acestep.pipeline_ace_step import ACEStepPipeline

        device_id = -1
        dtype = "float32"
        if torch.cuda.is_available():
            device_id = 0
            dtype = "bfloat16"

        pipeline = ACEStepPipeline(
            device_id=device_id,
            dtype=dtype,
            torch_compile=False,
            cpu_offload=False,
        )
        pipeline.load_checkpoint()

        seeds = [args.seed] if args.seed is not None else []

        with torch.inference_mode():
            result = pipeline(
                prompt=args.prompt,
                audio_duration=args.duration,
                infer_step=args.steps,
                guidance_scale=args.guidance,
                lyrics="",
                manual_seeds=seeds,
            )

        if not isinstance(result, list) or len(result) < 2:
            print(json.dumps({"status": "error", "message": f"Unexpected output: {result}"}))
            sys.exit(1)

        generated_path = result[0]
        if not generated_path or not os.path.exists(generated_path):
            print(json.dumps({"status": "error", "message": f"File not found: {generated_path}"}))
            sys.exit(1)

        shutil.copy2(generated_path, args.outfile)

        import torchaudio
        audio_tensor, sample_rate = torchaudio.load(args.outfile)
        duration = round(audio_tensor.shape[-1] / sample_rate, 2)

        print(json.dumps({"status": "ok", "path": os.path.abspath(args.outfile), "duration": duration}))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
