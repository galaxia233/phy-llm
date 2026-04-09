# 项目模块说明

## 项目结构

```
format/
├── config.py           # 配置模块
├── file_converter.py   # 文件转换模块
├── api_client.py       # API 客户端模块
├── answer_verifier.py  # 答案验证模块
├── system_prompts.py   # System Prompt 提示词集
├── test.py             # 测试脚本
├── requirements.txt    # 依赖列表
└── README_MODULES.md   # 本文件
```

## 模块说明

### 1. config.py - 配置模块

**职责**：集中管理所有配置常量和环境变量

**提供的内容**：
- `API_URL` - API 端点
- `API_KEY` - API 密钥（从环境变量读取）
- `DEFAULT_MODEL` - 默认模型
- `DEFAULT_TOLERANCE` - 验证误差容忍度
- `PDF_DPI` - PDF 转图片的 DPI
- `DEFAULT_MAX_RETRIES` - 默认最大重试次数
- `DEFAULT_TIMEOUT` - 默认超时时间
- `DEFAULT_MAX_TOKENS` - 默认最大 token 数
- `check_api_key()` - 检查 API key 是否已设置

**使用示例**：
```python
from config import API_KEY, DEFAULT_MODEL, check_api_key

check_api_key()  # 验证 API key
print(f"使用模型：{DEFAULT_MODEL}")
```

### 2. file_converter.py - 文件转换模块

**职责**：将 PDF 和 Word 文件转换为图片

**提供的函数**：
- `convert_pdf_to_images(path)` - PDF 转图片列表
- `convert_word_to_images(path)` - Word 转图片列表
- `is_supported_image(suffix)` - 判断是否是支持的图片格式
- `get_media_type(suffix)` - 获取文件后缀对应的 media type
- `IMAGE_MEDIA_MAP` - 图片格式映射字典

**使用示例**：
```python
from file_converter import convert_pdf_to_images

images = convert_pdf_to_images("document.pdf")
for img_bytes, name in images:
    print(f"页面：{name}, 大小：{len(img_bytes)} bytes")
```

### 3. api_client.py - API 客户端模块

**职责**：调用 AI API

**提供的函数**：
- `ask_ai(prompt, files, system, model, max_tokens, max_retries)` - 主要接口

**使用示例**：
```python
from api_client import ask_ai
from system_prompts import SystemPrompts

# 简单调用
ans = ask_ai("问题", files="image.png")

# 带 system prompt
ans = ask_ai("问题", system=SystemPrompts.PHYSICS_TEACHER)

# 多文件
ans = ask_ai("比较 [文件 1] 和 [文件 2]", files=["a.png", "b.pdf"])
```

### 4. answer_verifier.py - 答案验证模块

**职责**：验证 AI 回答的答案是否正确

**提供的函数**：
- `verify_answer(ai_answer, ref_answer, tolerance)` - 主验证函数
- `verify_answer_numeric(student, reference, tolerance)` - 数值验证
- `verify_answer_formula(student, reference)` - 公式验证

**使用示例**：
```python
from answer_verifier import verify_answer

# 数值答案
result = verify_answer(
    {"value": "9.8", "unit": ""},
    {"value": "9.81", "unit": ""}
)
print(result)  # {"is_correct": True, "method": "numeric"}

# 公式答案
result = verify_answer(
    {"value": "0.5*m*v*v", "unit": ""},
    {"value": "\\frac{1}{2}mv^2", "unit": ""}
)
print(result)  # {"is_correct": True, "method": "sympy"}
```

### 5. system_prompts.py - System Prompt 提示词集

**职责**：管理预定义的 system prompts

**提供的内容**：
- `SystemPrompts` - 枚举类
- `SYSTEM_PROMPTS` - 字典
- `get_system(name)` - 获取函数
- `list_prompts()` - 列出所有名称
- `print_prompts()` - 打印预览

**使用示例**：
```python
from system_prompts import SystemPrompts, get_system

# 枚举方式
ans = ask_ai("问题", system=SystemPrompts.PHYSICS_TEACHER)

# 字符串方式
ans = ask_ai("问题", system=get_system("physics_coach"))
```

### 6. test.py - 测试脚本

**职责**：演示各模块的使用方法和运行测试

**包含的测试**：
- `test_ask_ai_basic()` - 单张图片测试
- `test_ask_ai_multiple_files()` - 多文件测试
- `test_ask_ai_with_system()` - system prompt 测试
- `test_ask_ai_mixed_files()` - 混合文件测试
- `test_verify_numeric()` - 数值验证测试
- `test_verify_formula()` - 公式验证测试
- `test_verify_with_unit()` - 带单位验证测试

**运行测试**：
```bash
python test.py
```

## 模块依赖关系

```
config.py (无依赖)
    ↓
file_converter.py (依赖 config)
    ↓
api_client.py (依赖 config, file_converter)
    ↓
answer_verifier.py (依赖 config, api_client)
    
system_prompts.py (无依赖)

test.py (依赖以上所有模块)
```

## 导入示例

```python
# 所有模块都在根目录，直接导入
from config import API_KEY, DEFAULT_MODEL
from file_converter import convert_pdf_to_images
from api_client import ask_ai
from answer_verifier import verify_answer
from system_prompts import SystemPrompts, get_system
```

## 添加新功能

### 添加新的 System Prompt

在 `system_prompts.py` 中添加：

```python
# 在 SystemPrompts 枚举类中
MY_NEW_PROMPT = """你的提示词"""

# 在 SYSTEM_PROMPTS 字典中
"my_new": SystemPrompts.MY_NEW_PROMPT.value,
```

### 添加新的验证方法

在 `answer_verifier.py` 中添加函数，然后在 `verify_answer()` 中调用。

### 添加新的配置项

在 `config.py` 中添加常量，并在需要的模块中导入使用。