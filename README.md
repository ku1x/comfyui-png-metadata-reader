# ComfyUI PNG Metadata Reader

A custom ComfyUI node that reads and extracts workflow prompts embedded in PNG images.

## ⚠️ Important

**Do NOT use the standard "Load Image" node!** It converts PNG to tensor and loses metadata.

Use **"Load Image (With Metadata)"** node instead.

## Features

- **Load Image (With Metadata)** - Load PNG and preserve metadata
- **Read PNG Metadata (Path)** - Read metadata from file path string
- **Extract Prompt Values** - Parse workflow JSON to extract prompts, seed, steps, cfg, model

## Installation

### Method 1: Git Clone
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/ku1x/comfyui-png-metadata-reader.git
```

### Method 2: ComfyUI Manager
Search for "PNG Metadata Reader" and install.

## Usage

### Basic Workflow
```
[Load Image (With Metadata)]
         │
         ├── IMAGE → (use in other nodes)
         │
         ├── workflow_prompt ──→ [Extract Prompt Values]
         │                              │
         │                              ├── positive_prompt
         │                              ├── negative_prompt
         │                              ├── seed
         │                              ├── steps
         │                              ├── cfg
         │                              └── model_name
         │
         ├── workflow_ui
         │
         └── raw_metadata
```

### Nodes

#### Load Image (With Metadata)
- **Input**: File selector (like standard Load Image)
- **Output**: 
  - `image` - IMAGE tensor (same as standard Load Image)
  - `workflow_prompt` - The workflow JSON
  - `workflow_ui` - The UI layout JSON
  - `raw_metadata` - All metadata as JSON string

#### Extract Prompt Values
- **Input**: `workflow_prompt` string
- **Output**:
  - `positive_prompt` - Positive prompt text
  - `negative_prompt` - Negative prompt text
  - `seed` - Seed value
  - `steps` - Sampling steps
  - `cfg` - CFG scale
  - `model_name` - Model/checkpoint name

## Technical Details

ComfyUI stores workflow data in PNG `tEXt` chunks:
- `prompt` - The workflow JSON (node definitions and connections)
- `workflow` - The UI layout and positions

Standard "Load Image" node converts PNG to tensor, which loses all metadata.
This node preserves the metadata by reading it before conversion.

## Supported Nodes

The extractor recognizes:
- **Prompts**: CLIPTextEncode, PrimitiveString, PrimitiveStringMultiline
- **Samplers**: KSampler, KSamplerAdvanced
- **Models**: CheckpointLoader, UNETLoader

## License

MIT
