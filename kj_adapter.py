"""
KJ to Simple Readable Metadata Adapter

A simple adapter node that converts KJ nodes' output format
to work with the original Simple Readable Metadata-SG node.

Usage:
[Load Images From Folder (KJ)]
         │
         ├── image (IMAGE) ──────┐
         │                        │
         └── image_path (STRING) ─┤
                                  │
                                  ▼
              [KJ to Metadata Adapter]
                                  │
                                  ├── image (IMAGE)
                                  └── file_path (STRING)
                                  │
                                  ▼
              [Simple Readable Metadata-SG (原版)]
"""

import torch
import os
import folder_paths
from PIL import Image
import numpy as np


class KJToMetadataAdapter:
    """
    Adapter node to connect KJ nodes' output to Simple Readable Metadata-SG.
    
    Takes KJ's batch image and path list, outputs single image and file path
    for the original Simple Readable Metadata-SG node.
    
    Inputs:
        - image: IMAGE tensor from KJ nodes (batch)
        - image_path: STRING (list of paths) from KJ nodes
        - batch_index: Which image in the batch to process (default: 0)
    
    Outputs:
        - image: Single IMAGE for Simple Readable Metadata-SG
        - file_path: STRING path for Simple Readable Metadata-SG
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

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "file_path")
    FUNCTION = "adapt"
    OUTPUT_NODE = False

    @classmethod
    def VALIDATE_INPUTS(cls, image_path, **kwargs):
        # Accept both string and list
        return True

    def adapt(self, image, batch_index=0, image_path=""):
        """
        Convert KJ output to format compatible with Simple Readable Metadata-SG.
        
        Args:
            image: IMAGE tensor (batch) from KJ nodes
            batch_index: Which image in the batch to process
            image_path: Path string or list of paths from KJ nodes
        
        Returns:
            Tuple of (single_image, file_path_string)
        """
        print(f"[KJAdapter] === START ===")
        print(f"[KJAdapter] image shape: {image.shape}")
        print(f"[KJAdapter] batch_index: {batch_index}")
        print(f"[KJAdapter] image_path type: {type(image_path)}")
        
        # Get single image from batch
        batch_size = image.shape[0]
        if batch_index >= batch_size:
            batch_index = batch_size - 1
        
        single_image = image[batch_index:batch_index+1]
        print(f"[KJAdapter] Selected image index {batch_index}, shape: {single_image.shape}")
        
        # Get file path
        file_path_str = ""
        
        if isinstance(image_path, list):
            print(f"[KJAdapter] image_path is list with {len(image_path)} items")
            if batch_index < len(image_path):
                file_path_str = str(image_path[batch_index])
            elif len(image_path) > 0:
                file_path_str = str(image_path[0])
            print(f"[KJAdapter] Selected path: {file_path_str}")
        elif isinstance(image_path, str):
            file_path_str = image_path
            print(f"[KJAdapter] image_path is string: {file_path_str}")
        else:
            print(f"[KJAdapter] image_path is unexpected type: {type(image_path)}")
        
        return (single_image, file_path_str)


# Node registration
NODE_CLASS_MAPPINGS = {
    "KJToMetadataAdapter": KJToMetadataAdapter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "KJToMetadataAdapter": "KJ to Metadata Adapter",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
