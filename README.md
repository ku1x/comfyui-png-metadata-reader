# ComfyUI PNG Metadata Reader

A custom ComfyUI node that reads and extracts workflow prompts embedded in PNG images.

## Features

- Extract `prompt` JSON from PNG metadata
- Extract `workflow` JSON from PNG metadata
- Parse and pretty-print the workflow data
- Output as STRING for use in other nodes

## Installation

1. Copy this folder to your `ComfyUI/custom_nodes/` directory
2. Restart ComfyUI

## Usage

1. Add a "Load Image" node and load a ComfyUI-generated PNG
2. Add "Read PNG Workflow Prompt" node (under "Image Utilities")
3. Connect the IMAGE output to the node's input
4. Connect the STRING output to a "Show Text" node or use in other nodes

## Output

The node outputs the workflow JSON as a formatted string, containing:
- Node connections
- Parameter values
- Model names
- Seeds
- Prompts (positive/negative)
- And more...

## Technical Details

ComfyUI stores workflow data in PNG `tEXt` chunks:
- `prompt` - The workflow JSON (node definitions and connections)
- `workflow` - The UI layout and positions

## License

MIT
