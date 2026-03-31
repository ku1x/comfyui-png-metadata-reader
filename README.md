# ComfyUI PNG Metadata Reader

A custom ComfyUI node that reads and extracts workflow prompts embedded in PNG images.

## ✨ External Image Input Support!

Based on [ShammiG/ComfyUI-Simple_Readable_Metadata-SG](https://github.com/ShammiG/ComfyUI-Simple_Readable_Metadata-SG), modified to support **external IMAGE input** from nodes like **"Load Images From Folder (KJ)"**.

## Features

- **Simple Readable Metadata (External Image)-SG** - Accept IMAGE tensor + file_path string
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

### External Image Input (Recommended)

Connect from **"Load Images From Folder (KJ)"** or similar nodes:

```
[Load Images From Folder (KJ)]
         │
         ├── IMAGE ────────────────────┐
         │                              │
         └── file_path (STRING) ────────┤
                                        │
                                        ▼
                    [Simple Readable Metadata (External Image)-SG]
                                        │
                                        ├── Simple_Readable_Metadata
                                        ├── image (visual preview)
                                        ├── Positive_Prompt
                                        ├── Negative_Prompt
                                        ├── seed
                                        └── file_name_text
```

### Why Two Inputs?

| Input | Purpose |
|-------|---------|
| `image` (IMAGE) | Visual preview in ComfyUI, passed through from KJ nodes |
| `file_path` (STRING) | Read actual metadata from the original file |

**Note**: IMAGE tensors lose metadata during conversion. The `file_path` input allows reading metadata from the original file.

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

### Simple Readable Metadata (External Image)-SG
Modified from ShammiG's original node to accept external IMAGE input.

- **Inputs**:
  - `image` (IMAGE) - Image tensor from KJ nodes or similar
  - `file_path` (STRING) - Path to the original file for metadata reading
  - `emoji_in_readable_text` (BOOLEAN)
  - `show_info` (SELECT)
- **Outputs**: Same as original - metadata, image, mask, prompts, seed, etc.

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
- Modified to support external IMAGE input from KJ nodes

## License

MIT
