#!/usr/bin/env python3
"""SD3 Medium subprocess entry point for AI background image generation.

Outputs JSON to stdout. Designed for subprocess.run() invocation.
Called by ACP's image_gen.py via the sd3_env Python environment.
"""
import argparse
import json
import os
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--guidance", type=float, default=7.0)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--outfile", required=True)
    args = parser.parse_args()

    try:
        import torch
        from diffusers import StableDiffusion3Pipeline

        device = "cpu"
        dtype = torch.float32

        if torch.cuda.is_available():
            device = "cuda"
            dtype = torch.float16

        t0 = time.time()

        pipe = StableDiffusion3Pipeline.from_single_file(
            args.model_path,
            torch_dtype=dtype,
        )
        pipe = pipe.to(device)

        generator = None
        if args.seed is not None:
            generator = torch.Generator(device=device).manual_seed(args.seed)

        image = pipe(
            prompt=args.prompt,
            negative_prompt="",
            num_inference_steps=args.steps,
            guidance_scale=args.guidance,
            width=args.width,
            height=args.height,
            generator=generator,
        ).images[0]

        os.makedirs(os.path.dirname(os.path.abspath(args.outfile)), exist_ok=True)
        image.save(args.outfile)

        elapsed = round(time.time() - t0, 1)
        print(json.dumps({
            "status": "ok",
            "path": os.path.abspath(args.outfile),
            "elapsed_seconds": elapsed,
            "device": device,
        }))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
