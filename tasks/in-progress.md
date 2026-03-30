# 进行中 - ComfyUI PNG Metadata Reader

## TASK-001: 基础节点开发
- 负责人: Developer Agent
- 开始: 2026-03-29
- 状态: ✅ 完成
- 进展:
  - ✅ 创建 PNGMetadataReader 节点
  - ✅ 创建 PNGMetadataExtractor 节点（提取具体值）
  - ✅ 支持 prompt 和 workflow 两种元数据

## TASK-002: 测试节点
- 负责人: Developer Agent
- 开始: 待定
- 状态: ⏳ 待启动
- 描述: 用真实的 ComfyUI 生成的 PNG 图片测试节点

## TASK-003: 发布到 GitHub
- 负责人: Developer Agent
- 开始: 待定
- 状态: ⏳ 待启动
- 描述: 创建 GitHub 仓库并发布

---

## 节点功能

### 1. PNGMetadataReader
**输入**: IMAGE
**输出**:
- `workflow_prompt` - 完整的 workflow JSON
- `workflow_ui` - UI 布局 JSON
- `raw_metadata` - 原始元数据

### 2. PNGMetadataExtractor
**输入**: IMAGE
**输出**:
- `positive_prompt` - 正向提示词
- `negative_prompt` - 负向提示词
- `seed` - 种子值
- `steps` - 步数
- `model_name` - 模型名称

---

*创建时间: 2026-03-29 06:52 UTC*
