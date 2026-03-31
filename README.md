# ComfyUI PNG Metadata Reader

A custom ComfyUI node that reads and extracts workflow prompts embedded in PNG images.

## ✨ New: External Input Support!

Based on [ShammiG/ComfyUI-Simple_Readable_Metadata-SG](https://github.com/ShammiG/ComfyUI-Simple_Readable_Metadata-SG), modified to support **external file path input** instead of only internal file selector.

## Features

- **Simple Readable Metadata (External Path)-SG** - Accept file path string from other nodes
- **Batch Read Metadata (Folder)** - Process all images in a folder at once
- **Batch Metadata to Prompt List** - Extract all prompts from batch results
- **Load Image (With Metadata)** - Load single image and preserve metadata
- **Extract Prompt Values** - Parse workflow JSON for specific values

## Installation

### Method 1: Git Clone
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/ku1x/comfyui-png-metadata-reader.git
```

### Method 2: ComfyUI Manager
Search for "PNG Metadata Reader" and install.

## Usage

### External Path Input (New!)

Now you can connect a file path string from any node:

```
[Some Node with file path output]
         │
         └── STRING (file path) ──→ [Simple Readable Metadata (External Path)-SG]
                                              │
                                              ├── Simple_Readable_Metadata
                                              ├── image
                                              ├── Positive_Prompt
                                              ├── Negative_Prompt
                                              ├── seed
                                              └── file_name_text
```

### Batch Processing

```
[Batch Read Metadata (Folder)]
         │
         ├── folder_path: "/path/to/images"
         ├── file_pattern: "*.png"
         │
         └── all_metadata ──→ [Batch Metadata to Prompt List]
```

## Nodes

### Simple Readable Metadata (External Path)-SG
Modified from ShammiG's original node to accept external file path input.

- **Input**: `file_path` (STRING) - path to image file
- **Output**: Same as original - metadata, image, mask, prompts, seed, etc.

### Batch Read Metadata (Folder)
- **Inputs**:
  - `folder_path` - Path to folder containing images
  - `file_pattern` - Glob pattern (default: `*.png`)
  - `recursive` - Search subfolders (default: False)
- **Outputs**:
  - `all_metadata` - JSON with all extracted metadata
  - `summary` - Human-readable summary
  - `file_count` - Number of files processed

## Supported Formats

- **Images**: PNG, WEBP
- **Metadata**: ComfyUI, ForgeUI, Automatic1111

## Credits

- Original [Simple Readable Metadata-SG](https://github.com/ShammiG/ComfyUI-Simple_Readable_Metadata-SG) by [ShammiG](https://github.com/ShammiG)
- Modified to support external file path input

## License

MIT
