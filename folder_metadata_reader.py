"""
Batch Simple Readable Metadata

A node that reads metadata from ALL images in a folder.
Uses ComfyUI's built-in folder selection (like original Simple Readable Metadata-SG).

No need for KJ nodes - just select a folder and it processes all images.

Based on ShammiG's Simple Readable Metadata-SG
"""

import torch
import os
import folder_paths
from PIL import Image
import numpy as np
import json
import re


class BatchSimpleReadableMetadata:
    """
    Read metadata from ALL images in a folder.
    
    Features:
    - Built-in folder selection (like original)
    - Processes all PNG/WEBP files in the folder
    - Outputs combined metadata for all images
    - Extracts prompts, seeds, models, etc.
    """

    CATEGORY = "image/analysis"

    @classmethod
    def INPUT_TYPES(cls):
        # Get list of folders in input directory
        input_dir = folder_paths.get_input_directory()
        folders = []
        if os.path.exists(input_dir):
            for item in os.listdir(input_dir):
                item_path = os.path.join(input_dir, item)
                if os.path.isdir(item_path):
                    folders.append(item)
        
        return {
            "required": {
                "folder_name": (sorted(folders) if folders else ["[no folders - enter path below]"],),
            },
            "optional": {
                "custom_folder_path": ("STRING", {"default": "", "multiline": False}),
                "file_pattern": ("STRING", {"default": "*.png"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("Simple_Readable_Metadata", "all_metadata_json", "prompts_list", "file_count")
    FUNCTION = "read_folder"
    OUTPUT_NODE = True

    def read_folder(self, folder_name, custom_folder_path="", file_pattern="*.png"):
        """Read metadata from all images in the selected folder."""
        
        import glob
        
        # Determine folder path
        if custom_folder_path and os.path.isdir(custom_folder_path):
            folder_path = custom_folder_path
        else:
            input_dir = folder_paths.get_input_directory()
            folder_path = os.path.join(input_dir, folder_name)
        
        print(f"[BatchSimpleReadableMetadata] Folder path: {folder_path}")
        
        if not os.path.isdir(folder_path):
            return (f"Folder not found: {folder_path}\n\nTip: Put images in ComfyUI/input/your_folder/ or enter full path in custom_folder_path", "", "", 0)
        
        # Find all matching files
        files = glob.glob(os.path.join(folder_path, file_pattern))
        files.extend(glob.glob(os.path.join(folder_path, file_pattern.replace(".png", ".webp"))))
        files = sorted(set(files))
        
        if not files:
            return (f"No files matching '{file_pattern}' in {folder_path}", "", "", 0)
        
        print(f"[BatchSimpleReadableMetadata] Processing {len(files)} files in {folder_path}")
        
        all_metadata = {}
        all_prompts = []
        all_models = set()
        all_seeds = []
        
        for file_path in files:
            filename = os.path.basename(file_path)
            
            try:
                img = Image.open(file_path)
                file_data = {
                    "filename": filename,
                    "metadata": {}
                }
                
                if img.info:
                    # Extract prompt metadata
                    if "prompt" in img.info:
                        try:
                            prompt_data = json.loads(img.info["prompt"])
                            file_data["prompt_json"] = prompt_data
                            
                            # Parse ComfyUI format
                            positive, negative, seed, steps, cfg, model = self._parse_comfyui(prompt_data)
                            
                            file_data["positive_prompt"] = positive
                            file_data["negative_prompt"] = negative
                            file_data["seed"] = seed
                            file_data["steps"] = steps
                            file_data["cfg"] = cfg
                            file_data["model"] = model
                            
                            if positive:
                                all_prompts.append({
                                    "file": filename,
                                    "positive": positive,
                                    "negative": negative
                                })
                            if model and model != "N/A":
                                all_models.add(model)
                            if seed:
                                all_seeds.append(seed)
                                
                        except json.JSONDecodeError:
                            pass
                    
                    # A1111 format
                    if "parameters" in img.info and "positive_prompt" not in file_data:
                        params = img.info["parameters"]
                        positive, negative, seed, steps, cfg = self._parse_a1111(params)
                        file_data["positive_prompt"] = positive
                        file_data["negative_prompt"] = negative
                        file_data["seed"] = seed
                        file_data["steps"] = steps
                        file_data["cfg"] = cfg
                        
                        if positive:
                            all_prompts.append({
                                "file": filename,
                                "positive": positive,
                                "negative": negative
                            })
                
                all_metadata[filename] = file_data
                print(f"[BatchSimpleReadableMetadata] Processed: {filename}")
                
            except Exception as e:
                all_metadata[filename] = {"error": str(e)}
                print(f"[BatchSimpleReadableMetadata] Error processing {filename}: {e}")
        
        # Build summary outputs
        simple_readable = self._build_simple_readable_metadata(all_prompts, all_models, all_seeds, len(files))
        prompts_list = self._build_prompts_list(all_prompts)
        all_metadata_json = json.dumps(all_metadata, indent=2, ensure_ascii=False)
        
        return (simple_readable, all_metadata_json, prompts_list, len(files))

    def _build_prompts_list(self, all_prompts):
        """Build a simple list of all prompts for easy copying."""
        lines = []
        for p in all_prompts:
            lines.append(f"[{p['file']}]")
            lines.append(p['positive'])
            if p.get('negative'):
                lines.append(f"Negative: {p['negative']}")
            lines.append("")
        return "\n".join(lines)

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
                
                if "KSampler" in class_type:
                    seed = inputs.get("seed", inputs.get("noise_seed", 0))
                    steps = inputs.get("steps", 0)
                    cfg = inputs.get("cfg", 0.0)
                
                if class_type == "CLIPTextEncode":
                    text = inputs.get("text", "")
                    title = node_data.get("_meta", {}).get("title", "").lower()
                    if text:
                        if "negative" in title or "neg" in title:
                            negative = text
                        elif not positive:
                            positive = text
                
                if "CheckpointLoader" in class_type:
                    model = inputs.get("ckpt_name", "N/A")
                elif "UNETLoader" in class_type:
                    model = inputs.get("unet_name", "N/A")
        
        except Exception as e:
            print(f"[BatchSimpleReadableMetadata] Parse error: {e}")
        
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
            print(f"[BatchSimpleReadableMetadata] A1111 parse error: {e}")
        
        return positive, negative, seed, steps, cfg

    def _build_prompts_summary(self, all_prompts):
        """Build human-readable prompts summary (like original Simple Readable Metadata-SG)."""
        lines = []
        lines.append("=" * 60)
        lines.append("BATCH METADATA READER - SIMPLE READABLE OUTPUT")
        lines.append("=" * 60)
        lines.append("")
        
        for i, p in enumerate(all_prompts, 1):
            lines.append(f"--- IMAGE {i}: {p['file']} ---")
            lines.append("")
            lines.append("📝 POSITIVE PROMPT:")
            lines.append(f"  {p['positive']}")
            lines.append("")
            if p.get('negative'):
                lines.append("📝 NEGATIVE PROMPT:")
                lines.append(f"  {p['negative']}")
                lines.append("")
            lines.append("")
        
        return "\n".join(lines)

    def _build_models_summary(self, all_models, all_seeds, file_count):
        """Build models and stats summary."""
        lines = []
        lines.append("=" * 60)
        lines.append("STATISTICS")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Files processed: {file_count}")
        lines.append("")
        
        lines.append("🧠 MODELS USED:")
        for m in sorted(all_models):
            lines.append(f"  - {m}")
        lines.append("")
        
        if all_seeds:
            lines.append(f"🎯 Seeds range: {min(all_seeds)} - {max(all_seeds)}")
        
        return "\n".join(lines)
    
    def _build_simple_readable_metadata(self, all_prompts, all_models, all_seeds, file_count):
        """Build the main Simple_Readable_Metadata output (like original SG format)."""
        lines = []
        lines.append("=" * 60)
        lines.append("BATCH SIMPLE READABLE METADATA")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"📊 Total images processed: {file_count}")
        lines.append("")
        
        # Models section
        if all_models:
            lines.append("🧠 MODELS DETECTED:")
            for m in sorted(all_models):
                lines.append(f"  • {m}")
            lines.append("")
        
        # Prompts section
        lines.append("=" * 60)
        lines.append("📝 ALL PROMPTS DETECTED IN WORKFLOW")
        lines.append("=" * 60)
        lines.append("")
        
        for i, p in enumerate(all_prompts, 1):
            lines.append(f"─── IMAGE {i}: {p['file']} ───")
            lines.append("")
            lines.append("POSITIVE PROMPT:")
            # Wrap long prompts
            pos_lines = [p['positive'][j:j+80] for j in range(0, len(p['positive']), 80)]
            for pl in pos_lines:
                lines.append(f"  {pl}")
            lines.append("")
            
            if p.get('negative'):
                lines.append("NEGATIVE PROMPT:")
                neg_lines = [p['negative'][j:j+80] for j in range(0, len(p['negative']), 80)]
                for nl in neg_lines:
                    lines.append(f"  {nl}")
                lines.append("")
            lines.append("")
        
        # Seeds summary
        if all_seeds:
            lines.append("=" * 60)
            lines.append("🎯 SEEDS")
            lines.append("=" * 60)
            lines.append(f"  Range: {min(all_seeds)} - {max(all_seeds)}")
            lines.append(f"  Count: {len(all_seeds)}")
            lines.append("")
        
        return "\n".join(lines)


# Node registration
NODE_CLASS_MAPPINGS = {
    "BatchSimpleReadableMetadata": BatchSimpleReadableMetadata,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BatchSimpleReadableMetadata": "Batch Simple Readable Metadata",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
