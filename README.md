# ComfyUI PNG Metadata Reader

A custom ComfyUI node that reads and extracts workflow prompts embedded in PNG images.

## ✨ New: KJ to Metadata Adapter!

Instead of modifying the original Simple Readable Metadata-SG, we created an **adapter node** that converts KJ nodes' output format to work with the original node.

## Installation

### Step 1: Install Original Simple Readable Metadata-SG
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/ShammiG/ComfyUI-Simple_Readable_Metadata-SG.git
```

### Step 2: Install This Adapter
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/ku1x/comfyui-png-metadata-reader.git
```

### Step 3: Restart ComfyUI

## Usage

### KJ to Metadata Adapter

Connect KJ nodes to the original Simple Readable Metadata-SG:

```
[Load Images From Folder (KJ)]
         │
         ├── image (IMAGE) ──────────────┐
         │                                │
         └── image_path (STRING) ─────────┤
                                          │
                                          ▼
                      [KJ to Metadata Adapter]
                                          │
                                          ├── image (IMAGE)
                                          │
                                          └── file_path (STRING)
                                                  │
                                                  ▼
                      [Simple Readable Metadata-SG (原版)]
```

### Adapter Inputs

| Input | Type | Description |
|-------|------|-------------|
| `image` | IMAGE | Image tensor from KJ nodes (batch) |
| `image_path` | STRING | Path list from KJ nodes |
| `batch_index` | INT | Which image in the batch to process (default: 0) |

### Adapter Outputs

| Output | Type | Description |
|--------|------|-------------|
| `image` | IMAGE | Single image for Simple Readable Metadata-SG |
| `file_path` | STRING | File path string for Simple Readable Metadata-SG |

## Other Nodes

### Batch Read Metadata (Folder)
Process all images in a folder at once.

### Batch Metadata to Prompt List
Extract all prompts from batch results.

### Load Image (With Metadata)
Load single image and preserve metadata.

### Extract Prompt Values
Parse workflow JSON for specific values.

## Supported Formats

- **Images**: PNG, WEBP
- **Metadata**: ComfyUI, ForgeUI, Automatic1111

## Credits

- [Simple Readable Metadata-SG](https://github.com/ShammiG/ComfyUI-Simple_Readable_Metadata-SG) by [ShammiG](https://github.com/ShammiG)
- KJ to Metadata Adapter by KuAi

## License

MIT
