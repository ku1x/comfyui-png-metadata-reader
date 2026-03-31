"""
Simple Readable Metadata for KJ Nodes

A standalone node that reads metadata from images loaded by KJ nodes.
Does not require the original Simple Readable Metadata-SG.

Usage:
[Load Images From Folder (KJ)]
         │
         ├── image (IMAGE) ──────┐
         │                        │
         └── image_path (STRING) ─┤
                                  │
                                  ▼
              [Simple Readable Metadata (KJ)]
                                  │
                                  ├── Simple_Readable_Metadata
                                  ├── image
                                  ├── Positive_Prompt
                                  ├── Negative_Prompt
                                  ├── seed
                                  └── ...
"""

import torch
import os
import folder_paths
from PIL import Image
import numpy as np
import json
import re


class SimpleReadableMetadataKJ:
    """
    Read metadata from images loaded by KJ nodes.
    
    A complete standalone node that extracts:
    - Positive/Negative prompts
    - Seed, Steps, CFG
    - Sampler, Scheduler
    - Model name
    - And more...
    """

    CATEGORY = "image/analysis"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "batch_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
            },
            "optional": {
                "image_path": ("STRING", {"default": "", "forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING", "IMAGE", "STRING", "STRING", "INT", "INT", "FLOAT", "STRING", "STRING")
    RETURN_NAMES = ("Simple_Readable_Metadata", "image", "Positive_Prompt", "Negative_Prompt", "seed", "steps", "cfg", "model_name", "file_name")
    FUNCTION = "read_metadata"
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, image_path, **kwargs):
        return True

    def read_metadata(self, image, batch_index=0, image_path=""):
        """Read metadata from KJ nodes' output."""
        
        print(f"[SimpleReadableMetadataKJ] === START ===")
        print(f"[SimpleReadableMetadataKJ] image shape: {image.shape}")
        print(f"[SimpleReadableMetadataKJ] batch_index: {batch_index}")
        print(f"[SimpleReadableMetadataKJ] image_path type: {type(image_path)}")
        
        # Get single image from batch
        batch_size = image.shape[0]
        if batch_index >= batch_size:
            batch_index = batch_size - 1
        single_image = image[batch_index:batch_index+1]
        
        # Default values
        positive_prompt = ""
        negative_prompt = ""
        seed = 0
        steps = 0
        cfg = 0.0
        model_name = "N/A"
        file_name = "unknown"
        metadata_text = "No metadata found"
        
        # Get file path from KJ output
        file_path_str = ""
        if isinstance(image_path, list):
            print(f"[SimpleReadableMetadataKJ] image_path is list with {len(image_path)} items")
            if batch_index < len(image_path):
                file_path_str = str(image_path[batch_index])
            elif len(image_path) > 0:
                file_path_str = str(image_path[0])
        elif isinstance(image_path, str):
            file_path_str = image_path
        
        print(f"[SimpleReadableMetadataKJ] file_path: {file_path_str}")
        
        # Read metadata from file
        if file_path_str and os.path.isfile(file_path_str):
            try:
                img = Image.open(file_path_str)
                file_name = os.path.splitext(os.path.basename(file_path_str))[0]
                
                print(f"[SimpleReadableMetadataKJ] Opened file: {file_path_str}")
                print(f"[SimpleReadableMetadataKJ] Metadata keys: {list(img.info.keys()) if img.info else 'None'}")
                
                # Extract metadata
                if img.info:
                    if "prompt" in img.info:
                        try:
                            prompt_data = json.loads(img.info["prompt"])
                            positive_prompt, negative_prompt, seed, steps, cfg, model_name = self._parse_comfyui(prompt_data)
                            metadata_text = self._format_metadata(prompt_data, positive_prompt, negative_prompt, seed, steps, cfg, model_name)
                        except json.JSONDecodeError:
                            pass
                    
                    if "parameters" in img.info and not positive_prompt:
                        # A1111 format
                        params = img.info["parameters"]
                        positive_prompt, negative_prompt, seed, steps, cfg = self._parse_a1111(params)
                        metadata_text = self._format_metadata(None, positive_prompt, negative_prompt, seed, steps, cfg, model_name)
                
            except Exception as e:
                print(f"[SimpleReadableMetadataKJ] Error reading file: {e}")
                metadata_text = f"Error: {e}"
        else:
            metadata_text = f"File not found: {file_path_str}" if file_path_str else "No file path provided"
        
        print(f"[SimpleReadableMetadataKJ] Positive: {positive_prompt[:50]}..." if len(positive_prompt) > 50 else f"[SimpleReadableMetadataKJ] Positive: {positive_prompt}")
        print(f"[SimpleReadableMetadataKJ] Seed: {seed}, Steps: {steps}, CFG: {cfg}")
        
        return (metadata_text, single_image, positive_prompt, negative_prompt, int(seed), int(steps), float(cfg), model_name, file_name)

    def _parse_comfyui(self, prompt_data):
        """Parse ComfyUI workflow JSON."""
        positive = ""
        negative = ""
        seed = 0
        steps = 0
        cfg = 0.0
        model = "N/A"
        
        try:
            for node_id, node_data in prompt_data.items():
                class_type = node_data.get("class_type", "")
                inputs = node_data.get("inputs", {})
                
                # KSampler
                if "KSampler" in class_type:
                    seed = inputs.get("seed", inputs.get("noise_seed", 0))
                    steps = inputs.get("steps", 0)
                    cfg = inputs.get("cfg", 0.0)
                
                # CLIPTextEncode
                if class_type == "CLIPTextEncode":
                    text = inputs.get("text", "")
                    title = node_data.get("_meta", {}).get("title", "").lower()
                    if text:
                        if "negative" in title or "neg" in title:
                            negative = text
                        elif not positive:
                            positive = text
                
                # Model loader
                if "CheckpointLoader" in class_type:
                    model = inputs.get("ckpt_name", "N/A")
                elif "UNETLoader" in class_type:
                    model = inputs.get("unet_name", "N/A")
        
        except Exception as e:
            print(f"[SimpleReadableMetadataKJ] Error parsing ComfyUI: {e}")
        
        return positive, negative, seed, steps, cfg, model

    def _parse_a1111(self, params_text):
        """Parse A1111/WebUI format."""
        positive = ""
        negative = ""
        seed = 0
        steps = 0
        cfg = 0.0
        
        try:
            lines = params_text.strip().split('\n')
            for line in lines:
                if line.startswith("Negative prompt:"):
                    negative = line.replace("Negative prompt:", "").strip()
                elif re.search(r'Steps:\s*\d+', line):
                    # Extract params from this line
                    seed_match = re.search(r'Seed:\s*(\d+)', line)
                    if seed_match:
                        seed = int(seed_match.group(1))
                    steps_match = re.search(r'Steps:\s*(\d+)', line)
                    if steps_match:
                        steps = int(steps_match.group(1))
                    cfg_match = re.search(r'CFG scale:\s*([\d.]+)', line)
                    if cfg_match:
                        cfg = float(cfg_match.group(1))
                elif not negative and not re.search(r':', line):
                    positive += line + " "
            positive = positive.strip()
        
        except Exception as e:
            print(f"[SimpleReadableMetadataKJ] Error parsing A1111: {e}")
        
        return positive, negative, seed, steps, cfg

    def _format_metadata(self, prompt_data, positive, negative, seed, steps, cfg, model):
        """Format metadata for display."""
        lines = []
        lines.append("=== ComfyUI Generation Parameters ===")
        lines.append("")
        lines.append(f"🧠 Model: {model}")
        lines.append("")
        lines.append("🎯 Sampling Settings:")
        lines.append(f"  Seed: {seed}")
        lines.append(f"  Steps: {steps}")
        lines.append(f"  CFG: {cfg}")
        lines.append("")
        lines.append("📝 Prompts:")
        lines.append(f"  Positive: {positive[:200]}..." if len(positive) > 200 else f"  Positive: {positive}")
        if negative:
            lines.append(f"  Negative: {negative[:200]}..." if len(negative) > 200 else f"  Negative: {negative}")
        
        return "\n".join(lines)


# Node registration
NODE_CLASS_MAPPINGS = {
    "SimpleReadableMetadataKJ": SimpleReadableMetadataKJ,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SimpleReadableMetadataKJ": "Simple Readable Metadata (KJ)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
