# AI Magic 后端 API

这是 AI Magic 项目的后端 API 服务，使用 Python Flask 框架实现。该服务提供了三个主要的 AI 生成接口：文生图、图生视频以及文生视频。

## 功能概述

后端 API 提供以下功能：

1. **文生图**：根据文本描述和风格选择生成图像
2. **图生视频**：将上传的图片转换为具有不同效果的视频
3. **文生视频**：直接从文本描述生成视频内容

## 技术栈

- Python 3.8+
- Flask - Web 框架
- Flask-CORS - 处理跨域请求
- OpenCV - 图像处理和视频生成
- PIL (Pillow) - 图像处理
- NumPy - 科学计算

## 安装说明

1. 确保已安装 Python 3.8 或更高版本
2. 创建并激活虚拟环境（可选但推荐）:

```bash
# 创建虚拟环境
python -m venv venv

# 在 Windows 上激活
venv\Scripts\activate

# 在 macOS/Linux 上激活
source venv/bin/activate
```

3. 安装依赖项:

```bash
pip install -r requirements.txt
```

## 运行服务器

```bash
python app.py
```

服务器将在 `http://localhost:5000` 启动。

## API 端点

### 1. 文生图 API

- URL: `/api/text-to-image`
- 方法: POST
- 请求体:
  ```json
  {
    "prompt": "图像描述文本",
    "style": "realistic|cartoon|painting|sketch|anime"
  }
  ```
- 响应:
  ```json
  {
    "images": [
      "/static/generated/images/image1.jpg",
      "/static/generated/images/image2.jpg",
      "/static/generated/images/image3.jpg",
      "/static/generated/images/image4.jpg"
    ]
  }
  ```

### 2. 图生视频 API

- URL: `/api/image-to-video`
- 方法: POST
- 请求体: 多部分表单数据
  - `image`: 图片文件
  - `effect`: 视频效果 (zoom|pan|3d|animate)
  - `length`: 视频长度（秒）
- 响应:
  ```json
  {
    "video": "/static/generated/videos/video.mp4"
  }
  ```

### 3. 文生视频 API

- URL: `/api/text-to-video`
- 方法: POST
- 请求体:
  ```json
  {
    "prompt": "视频描述文本",
    "style": "realistic|3d|animation|artistic",
    "length": 10
  }
  ```
- 响应:
  ```json
  {
    "video": "/static/generated/videos/video.mp4"
  }
  ```

## 目录结构

```
backend/
├── app.py              # 主应用文件
├── requirements.txt    # 依赖项
├── static/             # 静态文件
│   ├── uploads/        # 上传的文件
│   └── generated/      # 生成的媒体文件
│       ├── images/     # 生成的图像
│       └── videos/     # 生成的视频
```

## 注意事项

- 当前实现使用占位图像和简单的视频效果模拟 AI 生成结果
- 在实际生产环境中，应替换为实际的 AI 模型 API 调用
- 服务配置了 CORS，允许来自任何源的前端调用 API

## 未来改进

- 集成真实的 AI 生成模型 API
- 添加用户认证和访问控制
- 实现生成历史记录功能
- 增加更多风格和效果选项
- 优化视频处理性能
