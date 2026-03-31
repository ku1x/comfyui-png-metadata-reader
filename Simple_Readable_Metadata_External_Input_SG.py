"""
Modified Simple Readable Metadata-SG with External Input Support

Original by ShammiG: https://github.com/ShammiG/ComfyUI-Simple_Readable_Metadata-SG
Modified to support external image input (from Upload Image node or file path)

Changes:
- Added SimpleReadableMetadataFromPath: Accept file path string as input
- Added SimpleReadableMetadataFromTensor: Accept IMAGE tensor with metadata preservation
"""

import torch
import os
import folder_paths
from PIL import Image, ImageOps
import numpy as np
import hashlib
import json
import re


class SimpleReadableMetadataFromPath:
    """
    Read metadata from an external file path input.
    Use this when you want to connect a file path string from another node.
    
    Input: file_path (STRING) - path to the image file
    Output: Same as original Simple Readable Metadata-SG
    """

    CATEGORY = "image/analysis"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"default": "", "multiline": False}),
                "emoji_in_readable_text": ("BOOLEAN", {"default": True}),
                "show_info": (["both", "properties", "metadata", "none"], {"default": "both"}),
            },
        }

    RETURN_TYPES = ("STRING", "IMAGE", "MASK", "STRING", "STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = ("Simple_Readable_Metadata", "image", "mask", "metadata_raw", "Positive_Prompt", "Negative_Prompt", "seed", "file_name_text")
    FUNCTION = "read_from_path"
    OUTPUT_NODE = True

    def is_node_reference(self, value):
        try:
            if isinstance(value, list) and len(value) == 2:
                if isinstance(value[0], (str, int)) and isinstance(value[1], int):
                    return True
        except:
            pass
        return False

    def safely_convert_to_string(self, value):
        try:
            if self.is_node_reference(value):
                return "N/A"
            if isinstance(value, str):
                return value
            elif isinstance(value, list):
                if len(value) > 0:
                    return self.safely_convert_to_string(value[0])
                return "N/A"
            elif value is None:
                return "N/A"
            else:
                return str(value)
        except:
            return "N/A"

    def safely_process_value(self, value):
        return self.safely_convert_to_string(value)

    def _get_prompt_data_from_image(self, img):
        try:
            if hasattr(img, 'info') and img.info:
                if "prompt" in img.info:
                    try:
                        prompt_str = img.info["prompt"]
                        if isinstance(prompt_str, str):
                            return json.loads(prompt_str)
                        return prompt_str
                    except:
                        pass
                if "exif" in img.info:
                    try:
                        exif_bytes = img.info["exif"]
                        if isinstance(exif_bytes, bytes):
                            exif_string = exif_bytes.decode('utf-8', errors='ignore')
                            if "prompt:" in exif_string:
                                prompt_start = exif_string.find("prompt:")
                                if prompt_start != -1:
                                    prompt_data = exif_string[prompt_start + 7:]
                                    prompt_data = prompt_data.split('\x00')[0]
                                    try:
                                        return json.loads(prompt_data)
                                    except:
                                        pass
                    except Exception as e:
                        print(f"Error parsing WebP EXIF for prompt: {e}")
        except Exception as e:
            print(f"Error extracting prompt data: {e}")
        return None

    def extract_model_name(self, img):
        model_name = "N/A"
        try:
            if not hasattr(img, 'info') or not img.info:
                return model_name
            prompt_data = self._get_prompt_data_from_image(img)
            if prompt_data:
                try:
                    for node_id, node_data in prompt_data.items():
                        class_type = node_data.get('class_type', '')
                        inputs = node_data.get('inputs', {})
                        if 'CheckpointLoader' in class_type and 'ckpt_name' in inputs:
                            model_name = inputs['ckpt_name']
                            break
                        if 'UNETLoader' in class_type and 'unet_name' in inputs:
                            model_name = f"{inputs['unet_name']} (UNET)"
                            break
                except Exception as e:
                    print(f"Error parsing prompt metadata: {e}")
            if model_name == "N/A" and 'workflow' in img.info:
                try:
                    workflow_data = json.loads(img.info['workflow'])
                    for node in workflow_data.get('nodes', []):
                        node_type = node.get('type', '')
                        if 'Checkpoint' in node_type or 'Loader' in node_type:
                            widgets = node.get('widgets_values', [])
                            if widgets and len(widgets) > 0:
                                model_name = widgets[0]
                                break
                except Exception as e:
                    print(f"Error parsing workflow metadata: {e}")
            if model_name == "N/A" and 'parameters' in img.info:
                try:
                    params = img.info['parameters']
                    model_pattern = r'Model:\s*([^,\n]+)'
                    match = re.search(model_pattern, params)
                    if match:
                        model_name = match.group(1).strip()
                except Exception as e:
                    print(f"Error parsing A1111 metadata: {e}")
        except Exception as e:
            print(f"Error extracting model metadata: {e}")
        return model_name

    def extract_generation_params(self, img):
        params = {
            'seed': 'N/A',
            'steps': 'N/A',
            'cfg': 'N/A',
            'sampler': 'N/A',
            'scheduler': 'N/A'
        }
        try:
            if not hasattr(img, 'info') or not img.info:
                return params
            prompt_data = self._get_prompt_data_from_image(img)
            if prompt_data:
                try:
                    for node_id, node_data in prompt_data.items():
                        class_type = node_data.get('class_type', '')
                        inputs = node_data.get('inputs', {})
                        if class_type == "KSampler":
                            params['seed'] = inputs.get('seed', 'N/A')
                            params['steps'] = inputs.get('steps', 'N/A')
                            params['cfg'] = inputs.get('cfg', 'N/A')
                            params['sampler'] = inputs.get('sampler_name', 'N/A')
                            params['scheduler'] = inputs.get('scheduler', 'N/A')
                            return params
                        if 'seed' in inputs or 'noise_seed' in inputs:
                            params['seed'] = inputs.get('seed', inputs.get('noise_seed', params['seed']))
                        if 'steps' in inputs:
                            params['steps'] = inputs.get('steps', params['steps'])
                        if 'cfg' in inputs:
                            params['cfg'] = inputs.get('cfg', params['cfg'])
                        if 'sampler_name' in inputs:
                            params['sampler'] = inputs.get('sampler_name', params['sampler'])
                        if 'scheduler' in inputs:
                            params['scheduler'] = inputs.get('scheduler', params['scheduler'])
                except Exception as e:
                    print(f"Error parsing ComfyUI generation params: {e}")
            if 'parameters' in img.info and any(v == 'N/A' for v in params.values()):
                try:
                    metadata_text = img.info['parameters']
                    seed_match = re.search(r'Seed:\s*(\d+)', metadata_text)
                    if seed_match:
                        params['seed'] = int(seed_match.group(1))
                    steps_match = re.search(r'Steps:\s*(\d+)', metadata_text)
                    if steps_match:
                        params['steps'] = int(steps_match.group(1))
                    cfg_match = re.search(r'CFG scale:\s*([\d.]+)', metadata_text)
                    if cfg_match:
                        params['cfg'] = float(cfg_match.group(1))
                    sampler_match = re.search(r'Sampler:\s*([^,\n]+)', metadata_text)
                    if sampler_match:
                        params['sampler'] = sampler_match.group(1).strip()
                    scheduler_match = re.search(r'Schedule type:\s*([^,\n]+)', metadata_text)
                    if scheduler_match:
                        params['scheduler'] = scheduler_match.group(1).strip()
                except Exception as e:
                    print(f"Error parsing A1111 generation params: {e}")
        except Exception as e:
            print(f"Error extracting generation parameters: {e}")
        return params

    def read_from_path(self, file_path, emoji_in_readable_text=True, show_info="both"):
        """Read metadata from external file path"""
        try:
            # Validate file path
            if not file_path or not os.path.exists(file_path):
                error_msg = f"File not found: {file_path}"
                return (error_msg, torch.zeros(1, 512, 512, 3), torch.zeros(512, 512), error_msg, "", "", 0, "error")
            
            img = Image.open(file_path)
            
            model_name = self.extract_model_name(img)
            gen_params = self.extract_generation_params(img)
            
            img = ImageOps.exif_transpose(img)
            metadata_raw = self.extract_raw_metadata(img)
            
            if img.mode == 'I':
                img = img.point(lambda i: i * (1 / 255))
            
            original_img = img
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            image_tensor = torch.from_numpy(np.array(img).astype(np.float32) / 255.0).unsqueeze(0)
            
            if 'A' in original_img.getbands():
                mask = np.array(original_img.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask)
            else:
                mask = torch.zeros((original_img.size[1], original_img.size[0]), dtype=torch.float32, device="cpu")
            
            # Build display info
            batch_size, height, width, channels = image_tensor.shape
            total_pixels = width * height
            resolution_mp = float(total_pixels / 1_000_000)
            
            try:
                file_size_bytes = os.path.getsize(file_path)
                file_size_mb = float(file_size_bytes) / (1024 * 1024)
                self._current_image_path = os.path.basename(file_path)
                self._current_file_size = file_size_mb
                file_name_text_without_ext = os.path.splitext(os.path.basename(file_path))[0]
            except:
                file_size_mb = 0.0
                file_name_text_without_ext = "unknown"
            
            def gcd(a, b):
                while b:
                    a, b = b, a % b
                return a
            
            def find_closest_standard_ratio(decimal_ratio):
                standard_ratios = [
                    (1.0, '1:1'), (1.25, '5:4'), (1.33333, '4:3'),
                    (1.5, '3:2'), (1.6, '16:10'), (1.66667, '5:3'),
                    (1.77778, '16:9'), (1.88889, '17:9'), (2.0, '2:1'),
                    (2.33333, '21:9'), (2.35, '2.35:1'), (2.39, '2.39:1'),
                    (2.4, '12:5'),
                ]
                closest_diff = float('inf')
                closest_ratio = None
                error_threshold = 0.05
                for std_value, std_string in standard_ratios:
                    diff = abs(std_value - decimal_ratio)
                    if diff < closest_diff:
                        closest_diff = diff
                        closest_ratio = std_string
                if closest_diff <= error_threshold:
                    return closest_ratio
                return None
            
            divisor = gcd(width, height)
            width_ratio = float(width // divisor)
            height_ratio = float(height // divisor)
            aspect_ratio_decimal = width / height
            closest_standard = find_closest_standard_ratio(aspect_ratio_decimal)
            
            self._last_width = width
            self._last_height = height
            self._last_resolution_mp = resolution_mp
            self._last_width_ratio = width_ratio
            self._last_height_ratio = height_ratio
            self._last_aspect_ratio_decimal = aspect_ratio_decimal
            self._last_closest_standard = closest_standard
            self._last_file_size_mb = file_size_mb
            
            lines = []
            line1 = f"{width}x{height} | {resolution_mp:.2f}MP "
            if closest_standard and closest_standard != f"{int(width_ratio)}:{int(height_ratio)}":
                line2 = f"Ratio: {int(width_ratio)}:{int(height_ratio)} or {aspect_ratio_decimal:.2f}:1 or ~{closest_standard}"
            else:
                line2 = f"Ratio: {int(width_ratio)}:{int(height_ratio)} or {aspect_ratio_decimal:.2f}:1"
            line3 = f"File Size: {file_size_mb:.2f}MB"
            
            lines = [line1, line2, line3, ""]
            lines.append(f"Model: {model_name}")
            lines.append(f"Seed: {gen_params['seed']} | Steps: {gen_params['steps']} | CFG: {gen_params['cfg']}")
            lines.append(f"Sampler: {gen_params['sampler']} | Scheduler: {gen_params['scheduler']}")
            
            Simple_Readable_Metadata, positive, negative = self.parse_metadata(metadata_raw, emoji_in_readable_text)
            
            seed_value = gen_params['seed']
            if seed_value == 'N/A' or seed_value is None:
                seed_int = 0
            else:
                try:
                    seed_int = int(seed_value)
                except (ValueError, TypeError):
                    seed_int = 0
            
            return {
                "ui": {"text": lines},
                "result": (Simple_Readable_Metadata, image_tensor, mask, metadata_raw, positive, negative, seed_int, file_name_text_without_ext)
            }
        
        except Exception as e:
            print(f"Error in read_from_path: {e}")
            raise

    def extract_raw_metadata(self, img):
        png_info = img.info if hasattr(img, 'info') else {}
        if not png_info:
            return "No metadata found in image"
        if "prompt" in png_info:
            try:
                prompt_data = png_info["prompt"]
                if isinstance(prompt_data, str):
                    json.loads(prompt_data)
                    return prompt_data
                else:
                    return json.dumps(prompt_data)
            except:
                pass
        if "parameters" in png_info:
            return png_info["parameters"]
        if "exif" in png_info:
            try:
                exif_bytes = png_info["exif"]
                if isinstance(exif_bytes, bytes):
                    exif_string = exif_bytes.decode('utf-8', errors='ignore')
                    if "prompt:" in exif_string:
                        prompt_start = exif_string.find("prompt:")
                        if prompt_start != -1:
                            prompt_data = exif_string[prompt_start + 7:]
                            prompt_data = prompt_data.split('\x00')[0]
                            try:
                                json.loads(prompt_data)
                                return prompt_data
                            except:
                                pass
            except Exception as e:
                print(f"Error parsing WebP EXIF metadata: {e}")
        if hasattr(img, 'getexif'):
            try:
                exif_data = img.getexif()
                if exif_data:
                    user_comment = exif_data.get(0x9286)
                    if user_comment:
                        if isinstance(user_comment, bytes):
                            user_comment = user_comment.decode('utf-8', errors='ignore')
                        try:
                            json.loads(user_comment)
                            return user_comment
                        except:
                            return user_comment
            except Exception as e:
                print(f"Error reading EXIF via getexif(): {e}")
        return "No ComfyUI or WebUI format metadata found. Image may be from a different source."

    def parse_metadata(self, metadata_raw, include_emojis=True):
        try:
            if isinstance(metadata_raw, (bytes, bytearray)):
                try:
                    metadata_raw = metadata_raw.decode("utf-8", errors="ignore")
                except Exception:
                    metadata_raw = str(metadata_raw)
            metadata_raw = self.safely_process_value(metadata_raw)
            format_type = self.detect_format(metadata_raw)
            if format_type == "comfyui":
                Simple_Readable_Metadata = self.parse_comfyui_format(
                    metadata_raw,
                    include_emojis,
                    image_path=getattr(self, '_current_image_path', None),
                    file_size_mb=getattr(self, '_current_file_size', None)
                )
            elif format_type == "webui":
                Simple_Readable_Metadata = self.parse_webui_format(metadata_raw, include_emojis)
            else:
                Simple_Readable_Metadata = "Unable to detect metadata format."
            positive, negative = self.extract_individual_params(metadata_raw, format_type)
            positive = self.safely_convert_to_string(positive)
            negative = self.safely_convert_to_string(negative)
            return (Simple_Readable_Metadata, positive, negative)
        except Exception as e:
            print(f"Error in parse_metadata: {e}")
            return (f"Error parsing metadata: {str(e)}", "N/A", "N/A")

    def detect_format(self, text):
        try:
            text = self.safely_process_value(text).strip()
            if text.startswith("Prompt: "):
                text = text[8:]
            try:
                json.loads(text)
                return "comfyui"
            except json.JSONDecodeError:
                pass
            if (re.search(r'Steps:\s*\d+', text) or 
                re.search(r'Sampler:\s*\w+', text) or 
                re.search(r'CFG scale:\s*[\d.]+', text)):
                return "webui"
            return "unknown"
        except Exception as e:
            print(f"Error detecting format: {e}")
            return "unknown"

    def parse_webui_format(self, text, include_emojis=True):
        try:
            text = self.safely_process_value(text)
            emoji_map = {
                "sampling": "🎯", "dimensions": "📏", "prompts": "📝",
                "models": "🧠", "lora": "🎨", "advanced": "⚙️"
            } if include_emojis else {k: "" for k in ["sampling", "dimensions", "prompts", "models", "lora", "advanced"]}
            
            output = []
            output.append("=== WebUI Forge/A1111 Generation Parameters ===\n")
            
            lines = text.strip().split('\n')
            positive_prompt = ""
            negative_prompt = ""
            metadata_line = ""
            
            for i, line in enumerate(lines):
                if line.startswith("Negative prompt:"):
                    negative_prompt = line.replace("Negative prompt:", "").strip()
                elif re.search(r'Steps:\s*\d+', line):
                    metadata_line = line
                elif not metadata_line and not line.startswith("Negative prompt:"):
                    positive_prompt += line + " "
            
            positive_prompt = positive_prompt.strip()
            model_name_display = "N/A"
            if metadata_line:
                model_match = re.search(r'Model:\s*([^,\n]+)', metadata_line)
                if model_match:
                    model_name_display = model_match.group(1).strip()
            
            output.append(f"{emoji_map['models']} MODEL: {model_name_display}\n")
            output.append(f"{emoji_map['prompts']} PROMPTS:\n")
            output.append(f"  Positive:\n           {positive_prompt if positive_prompt else '(empty)'}\n")
            if negative_prompt:
                output.append(f"  Negative:\n           {negative_prompt}")
            output.append("")
            
            if metadata_line:
                params = {}
                patterns = {
                    'steps': r'Steps:\s*(\d+)',
                    'sampler': r'Sampler:\s*([^,]+)',
                    'cfg': r'CFG scale:\s*([\d.]+)',
                    'seed': r'Seed:\s*(\d+)',
                    'size': r'Size:\s*(\d+x\d+)',
                    'model': r'Model:\s*([^,]+)',
                }
                for key, pattern in patterns.items():
                    match = re.search(pattern, metadata_line)
                    if match:
                        params[key] = match.group(1).strip()
                
                output.append(f"{emoji_map['sampling']} SAMPLING SETTINGS:")
                if 'seed' in params:
                    output.append(f"  Seed: {params['seed']}")
                if 'steps' in params:
                    output.append(f"  Steps: {params['steps']}")
                if 'cfg' in params:
                    output.append(f"  CFG Scale: {params['cfg']}")
                if 'sampler' in params:
                    output.append(f"  Sampler: {params['sampler']}")
                output.append("")
            
            return "\n".join(output)
        except Exception as e:
            return f"Error parsing WebUI metadata: {str(e)}"

    def parse_comfyui_format(self, metadata_raw, include_emojis=True, image_path=None, file_size_mb=None):
        try:
            metadata_raw = self.safely_process_value(metadata_raw)
            clean_text = metadata_raw.strip()
            if clean_text.startswith("Prompt: "):
                clean_text = clean_text[8:]
            try:
                data = json.loads(clean_text)
            except json.JSONDecodeError as e:
                return f"Error parsing JSON: {str(e)}"
            
            output = []
            emoji_map = {
                "sampling": "🎯", "dimensions": "📏", "prompts": "📝",
                "models": "🧠", "lora": "🎨", "advanced": "⚙️"
            } if include_emojis else {k: "" for k in ["sampling", "dimensions", "prompts", "models", "lora", "advanced"]}
            
            output.append("=== ComfyUI Generation Parameters ===\n")
            
            # Extract model
            model_name_display = "N/A"
            for node_id, node_data in data.items():
                class_type = node_data.get("class_type", "")
                inputs = node_data.get("inputs", {})
                if 'CheckpointLoader' in class_type and 'ckpt_name' in inputs:
                    model_name_display = inputs['ckpt_name']
                    break
                elif 'UNETLoader' in class_type and 'unet_name' in inputs:
                    model_name_display = f"{inputs['unet_name']} (UNET)"
                    break
            
            output.append(f"{emoji_map['models']} MODEL: {model_name_display}")
            output.append("")
            
            # Extract sampling params
            sampling_params = {'seed': 'N/A', 'steps': 'N/A', 'cfg': 'N/A', 'sampler': 'N/A', 'scheduler': 'N/A'}
            for node_id, node_data in data.items():
                if node_data.get("class_type") == "KSampler":
                    ksampler_data = node_data.get("inputs", {})
                    sampling_params['seed'] = self.safely_process_value(ksampler_data.get('seed', 'N/A'))
                    sampling_params['steps'] = self.safely_process_value(ksampler_data.get('steps', 'N/A'))
                    sampling_params['cfg'] = self.safely_process_value(ksampler_data.get('cfg', 'N/A'))
                    sampling_params['sampler'] = self.safely_process_value(ksampler_data.get('sampler_name', 'N/A'))
                    sampling_params['scheduler'] = self.safely_process_value(ksampler_data.get('scheduler', 'N/A'))
                    break
            
            output.append(f"{emoji_map['sampling']} SAMPLING SETTINGS:")
            output.append(f"  Seed: {sampling_params['seed']}")
            output.append(f"  Steps: {sampling_params['steps']}")
            output.append(f"  CFG Scale: {sampling_params['cfg']}")
            output.append(f"  Sampler: {sampling_params['sampler']}")
            output.append(f"  Scheduler: {sampling_params['scheduler']}")
            output.append("")
            
            # Extract prompts
            positive_prompt = ""
            negative_prompt = ""
            for node_id, node_data in data.items():
                class_type = node_data.get("class_type", "")
                inputs = node_data.get("inputs", {})
                if "CLIPTextEncode" in class_type:
                    title = node_data.get("_meta", {}).get("title", "").lower()
                    text_value = inputs.get("text", "")
                    if self.is_node_reference(text_value):
                        continue
                    text_value = self.safely_process_value(text_value)
                    if not text_value or not text_value.strip():
                        continue
                    is_negative = "negative" in title or "neg" in title
                    if is_negative:
                        negative_prompt = text_value
                    else:
                        positive_prompt = text_value
            
            output.append(f"{emoji_map['prompts']} PROMPTS:\n")
            output.append(f"  Positive:\n           {positive_prompt if positive_prompt else '(empty)'}\n")
            if negative_prompt:
                output.append(f"  Negative:\n           {negative_prompt}")
            
            return "\n".join(output)
        except Exception as e:
            return f"Error processing parameters: {str(e)}"

    def extract_individual_params(self, text, format_type):
        positive = ""
        negative = ""
        try:
            text = self.safely_process_value(text)
            if format_type == "comfyui":
                clean_text = text.strip()
                if clean_text.startswith("Prompt: "):
                    clean_text = clean_text[8:]
                try:
                    data = json.loads(clean_text)
                    for node_id, node_data in data.items():
                        class_type = node_data.get("class_type", "")
                        if "CLIPTextEncode" in class_type:
                            title = node_data.get("_meta", {}).get("title", "").lower()
                            text_content = node_data.get("inputs", {}).get("text", "")
                            if self.is_node_reference(text_content):
                                continue
                            text_content = self.safely_process_value(text_content)
                            if not text_content or not text_content.strip():
                                continue
                            is_negative = "negative" in title or "neg" in title
                            if is_negative:
                                negative = text_content
                            else:
                                positive = text_content
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
            elif format_type == "webui":
                lines = text.strip().split('\n')
                for line in lines:
                    if line.startswith("Negative prompt:"):
                        negative = line.replace("Negative prompt:", "").strip()
                    elif not re.search(r'Steps:\s*\d+', line) and not line.startswith("Negative prompt:"):
                        positive += line + " "
                positive = positive.strip()
        except Exception as e:
            print(f"Error in extract_individual_params: {e}")
        return positive, negative


# Node registration
NODE_CLASS_MAPPINGS = {
    "SimpleReadableMetadataFromPath": SimpleReadableMetadataFromPath,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SimpleReadableMetadataFromPath": "Simple Readable Metadata (External Path)-SG",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
