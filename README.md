# ComfyUI PNG Metadata Reader

A custom ComfyUI node that reads and extracts workflow prompts embedded in PNG images.

## ✨ New: Batch Folder Processing!

Now supports batch processing images from a folder, inspired by [ShammiG/ComfyUI-Simple_Readable_Metadata-SG](https://github.com/ShammiG/ComfyUI-Simple_Readable_Metadata-SG).

## Features

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

### Batch Processing (New!)

```
[Batch Read Metadata (Folder)]
         │
         ├── folder_path: "/path/to/images"
         ├── file_pattern: "*.png"
         ├── recursive: True/False
         │
         ├── all_metadata ──→ [Batch Metadata to Prompt List]
         │                              │
         │                              ├── prompts_text
         │                              ├── prompts_json
         │                              └── count
         │
         ├── summary (human-readable summary)
         │
         └── file_count
```

### Single Image

```
[Load Image (With Metadata)]
         │
         ├── IMAGE → (use in other nodes)
         │
         └── workflow_prompt ──→ [Extract Prompt Values]
                                        │
                                        ├── positive_prompt
                                        ├── negative_prompt  
                                        ├── seed
                                        ├── steps
                                        ├── cfg
                                        └── model_name
```

## Nodes

### Batch Read Metadata (Folder)
- **Inputs**:
  - `folder_path` - Path to folder containing images
  - `file_pattern` - Glob pattern (default: `*.png`)
  - `recursive` - Search subfolders (default: False)
- **Outputs**:
  - `all_metadata` - JSON with all extracted metadata
  - `summary` - Human-readable summary
  - `file_count` - Number of files processed

### Batch Metadata to Prompt List
- **Inputs**:
  - `all_metadata` - Output from Batch Read Metadata
  - `output_type` - "positive", "negative", or "both"
- **Outputs**:
  - `prompts_text` - Plain text list of prompts
  - `prompts_json` - JSON array of prompts
  - `count` - Number of prompts extracted

### Load Image (With Metadata)
- **Input**: File selector (like standard Load Image)
- **Output**: 
  - `image` - IMAGE tensor
  - `workflow_prompt` - The workflow JSON
  - `workflow_ui` - The UI layout JSON
  - `raw_metadata` - All metadata as JSON string

### Extract Prompt Values
- **Input**: `workflow_prompt` string
- **Output**:
  - `positive_prompt` - Positive prompt text
  - `negative_prompt` - Negative prompt text
  - `seed` - Seed value
  - `steps` - Sampling steps
  - `cfg` - CFG scale
  - `model_name` - Model/checkpoint name

## Supported Formats

- **Images**: PNG, WEBP
- **Metadata**: ComfyUI, ForgeUI, Automatic1111

## Technical Details

ComfyUI stores workflow data in PNG `tEXt` chunks:
- `prompt` - The workflow JSON (node definitions and connections)
- `workflow` - The UI layout and positions

Standard "Load Image" node converts PNG to tensor, which loses all metadata.
These nodes preserve the metadata by reading it before conversion.

## License

MIT
