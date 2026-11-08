from flask import Flask, request, jsonify, send_from_directory
import os
import time
import uuid
import urllib.request
import json
import base64
import io
import requests
from dotenv import load_dotenv
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import random
import traceback
from openai import OpenAI
from huggingface_hub import InferenceClient

# 加载环境变量
load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)  # 允许跨域请求，这样前端可以调用API

# 确保上传和生成目录存在
UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
GENERATED_IMAGES = os.path.join(app.static_folder, 'generated', 'images')
GENERATED_VIDEOS = os.path.join(app.static_folder, 'generated', 'videos')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_IMAGES, exist_ok=True)
os.makedirs(GENERATED_VIDEOS, exist_ok=True)

# 可以访问静态文件
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# 1. 文生图 API
@app.route('/api/text-to-image', methods=['POST'])
def text_to_image():
    data = request.json
    prompt = data.get('prompt', '')
    style = data.get('style', 'realistic')
    
    if not prompt:
        return jsonify({'error': '请提供文字描述'}), 400
    
    # 风格处理词典
    style_prompts = {
        'realistic': ("高清真实照片风格", "High-definition realistic photo of"),
        'cartoon': ("卡通风格", "Cartoon style illustration of"),
        'painting': ("艺术绘画风格", "Artistic painting of"),
        'sketch': ("素描风格", "Pencil sketch of"),
        'anime': ("动漫风格", "Anime style illustration of")
    }
    
    # 获取风格前缀
    chinese_style = style_prompts.get(style, ('', ''))[0]
    english_style = style_prompts.get(style, ('', ''))[1]
    
    # 中文提示词用于日志和界面显示
    enhanced_prompt_zh = f"{chinese_style} - {prompt}"
    # 英文提示词用于 AI 生成
    enhanced_prompt_en = f"{english_style} {prompt}"
    
    # 准备返回的图像 URL列表
    image_urls = []
    print(f"生成图像: {enhanced_prompt_zh}")
    print(f"AI 提示词: {enhanced_prompt_en}")
    
    # 初始化AI客户端
    use_openai_api = False
    use_huggingface_api = False
    openai_client = None
    huggingface_client = None
    
    # 尝试初始化Hugging Face客户端
    try:
        huggingface_api_key = os.environ.get('HUGGINGFACE_API_KEY')
        if huggingface_api_key:
            huggingface_client = InferenceClient(token=huggingface_api_key)
            use_huggingface_api = True
            print("尝试使用 Hugging Face API 生成图像")
        else:
            print("警告: 未设置HUGGINGFACE_API_KEY环境变量")
    except Exception as e:
        print(f"Hugging Face 客户端初始化错误: {str(e)}")
        use_huggingface_api = False
    
    # 尝试初始化OpenAI客户端(作为备用选项)
    try:
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if openai_api_key:
            openai_client = OpenAI()
            use_openai_api = True
            print("尝试使用 OpenAI DALL-E API 作为备用选项")
        else:
            print("警告: 未设置OPENAI_API_KEY环境变量")
    except Exception as e:
        print(f"OpenAI 客户端初始化错误: {str(e)}")
        use_openai_api = False
        
    # 检查是否至少有一个API可用
    use_ai_api = use_huggingface_api or use_openai_api
    
    # 生成 4 张图像
    for i in range(4):
        try:
            print(f"生成图像 {i+1}/4")
            filename = f"{uuid.uuid4()}.jpg"
            image_path = os.path.join(GENERATED_IMAGES, filename)
            
            # 尝试使用AI API 生成图像
            if use_ai_api:
                # 准备提示词
                has_chinese = any(u'\u4e00' <= char <= u'\u9fff' for char in prompt)
                translated_prompt = None
                final_prompt = enhanced_prompt_en
                
                # 如果有中文，尝试翻译
                if has_chinese and use_openai_api:
                    try:
                        # 使用OpenAI翻译提示词
                        translation_response = openai_client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a translator that translates Chinese to English. Only provide the translation without any additional text."},
                                {"role": "user", "content": f"Translate this to English: {prompt}"}
                            ],
                            max_tokens=50,
                            temperature=0.3
                        )
                        # 提取翻译结果
                        translated_prompt = translation_response.choices[0].message.content.strip()
                        print(f"翻译提示词: '{prompt}' -> '{translated_prompt}'")
                        final_prompt = f"{english_style} {translated_prompt}"
                    except Exception as trans_err:
                        print(f"翻译提示词失败: {str(trans_err)}, 使用原始提示词")
                
                # 1. 首先尝试使用 Hugging Face API
                if use_huggingface_api:
                    try:
                        # 使用翻译后的提示词或原始提示词
                        prompt_to_use = final_prompt
                        print(f"Hugging Face 生成图像: {prompt_to_use}")
                        
                        # 使用稳定性最高的模型
                        model_id = "stabilityai/stable-diffusion-xl-base-1.0"  # 或使用 "runwayml/stable-diffusion-v1-5"
                        
                        # 调用Hugging Face模型 API
                        image_bytes = huggingface_client.text_to_image(
                            prompt=prompt_to_use,
                            model=model_id,
                            negative_prompt="blurry, bad quality, distorted"
                        )
                        
                        # 将生成的图像保存到文件
                        print(f"Hugging Face 模型生成成功，保存图像")
                        # 处理返回的是PIL Image对象的情况
                        if hasattr(image_bytes, 'save'):
                            # 这是PIL Image对象
                            image_bytes.save(image_path)
                        else:
                            # 这是字节对象
                            with open(image_path, "wb") as f:
                                f.write(image_bytes)
                        
                        # 添加到返回列表
                        relative_url = f"/static/generated/images/{filename}"
                        image_urls.append(relative_url)
                        print(f"Hugging Face 图像生成完成 {i+1}/4")
                        continue  # 成功生成，跳过备用方案
                    except Exception as hf_err:
                        error_message = str(hf_err)
                        print(f"Hugging Face API 调用失败: {error_message}")
                        # 如果是配额限制或内容策略问题，切换到备用方案
                        if "rate" in error_message.lower() and "limit" in error_message.lower():
                            print("Hugging Face API速率限制，尝试其他方案")
                            use_huggingface_api = False
                
                # 2. 如果Hugging Face失败，尝试使用 OpenAI API
                if use_openai_api and not use_huggingface_api:
                    try:
                        print(f"OpenAI DALL-E 生成图像: {final_prompt}")
                        
                        # 创建图像生成请求
                        response = openai_client.images.generate(
                            model="dall-e-2",  # 使用 DALL-E 2模型提升成功率
                            prompt=final_prompt,
                            n=1,
                            size="512x512",
                            response_format="url"
                        )
                        
                        # 下载生成的图像
                        ai_image_url = response.data[0].url
                        print(f"DALL-E 生成成功，下载图像: {ai_image_url}")
                        urllib.request.urlretrieve(ai_image_url, image_path)
                        
                        # 添加到返回列表
                        relative_url = f"/static/generated/images/{filename}"
                        image_urls.append(relative_url)
                        print(f"DALL-E 图像生成完成 {i+1}/4")
                        continue  # 成功生成，跳过备用方案
                    except Exception as ai_err:
                        # 详细记录API错误
                        error_message = str(ai_err)
                        print(f"OpenAI API 调用失败: {error_message}")
                        
                        # 检查错误类型
                        if "content_policy_violation" in error_message.lower() or "image_generation_user_error" in error_message.lower():
                            print("提示词可能违反内容政策或格式不正确，尝试下一张图像")
                            # 如果是内容政策问题，可能只是当前提示词的问题，后续仍可尝试API
                        elif "rate" in error_message.lower() and "limit" in error_message.lower():
                            print("API速率限制，切换到备用方案")
                            use_ai_api = False  # 停止尝试使用API
                        else:
                            # 其他API错误，继续尝试后续图像
                            print("未知API错误，继续尝试")
                            # 如果连续失败多次，可以考虑禁用API
                            if i >= 2:  # 如果前两次尝试都失败
                                use_ai_api = False  # 停止尝试使用API
            
            # 如果 API 调用失败或没有使用 API，使用 Picsum 生成占位图像
            if not use_ai_api:
                # 为每种风格使用不同的种子
                style_id = {'realistic': 1, 'cartoon': 2, 'painting': 3, 'sketch': 4, 'anime': 5}.get(style, 1)
                seed = random.randint(1, 1000) + (style_id * 100) + i
                
                # 下载图像
                image_url = f"https://picsum.photos/seed/{seed}/512/512"
                print(f"使用备用图像: {image_url}")
                urllib.request.urlretrieve(image_url, image_path)
                
                # 添加到返回列表
                relative_url = f"/static/generated/images/{filename}"
                image_urls.append(relative_url)
                print(f"成功生成备用图像 {i+1}/4")
            
        except Exception as e:
            print(f"图像生成失败: {str(e)}")
            
            try:
                # 创建带文本的备用图像
                blank_image = Image.new('RGB', (512, 512), color=(240, 240, 240))
                draw = ImageDraw.Draw(blank_image)
                
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except Exception:
                    font = ImageFont.load_default()
                
                # 添加文本
                draw.text((100, 200), f"AI生成图像 - {chinese_style}", fill=(80, 80, 80), font=font)
                draw.text((100, 250), f"{prompt[:30]}...", fill=(80, 80, 80), font=font)
                
                # 保存图像
                filename = f"text_{uuid.uuid4()}.jpg"
                image_path = os.path.join(GENERATED_IMAGES, filename)
                blank_image.save(image_path)
                
                relative_url = f"/static/generated/images/{filename}"
                image_urls.append(relative_url)
                print("创建了文本备用图像")
                
            except Exception as blank_err:
                print(f"创建文本图像失败: {str(blank_err)}")
                # 使用默认占位图像
                relative_url = f"/static/img/placeholder_{i+1}.jpg"
                image_urls.append(relative_url)
    
    # 返回图像 URL 列表
    return jsonify({"images": image_urls})

# 2. 图生视频 API
@app.route('/api/image-to-video', methods=['POST'])
def image_to_video():
    # 确保有文件
    if 'image' not in request.files:
        return jsonify({'error': '未找到图片文件'}), 400
    
    file = request.files['image']
    effect = request.form.get('effect', 'zoom')
    video_length = int(request.form.get('length', 5))
    
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 保存上传的图片
    image_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    image_path = os.path.join(UPLOAD_FOLDER, image_filename)
    file.save(image_path)
    
    # 生成视频文件名和路径
    video_filename = f"{uuid.uuid4()}.mp4"
    video_path = os.path.join(GENERATED_VIDEOS, video_filename)
    
    # 调用转换函数（这里模拟转换过程）
    success = create_video_from_image(image_path, video_path, effect, video_length)
    
    if not success:
        return jsonify({'error': '视频生成失败'}), 500
    
    # 返回视频URL
    video_url = f"/static/generated/videos/{video_filename}"
    return jsonify({"video": video_url})

# 3. 文生视频 API
@app.route('/api/text-to-video', methods=['POST'])
def text_to_video():
    data = request.json
    prompt = data.get('prompt', '')
    style = data.get('style', 'realistic')
    video_length = int(data.get('length', 5))  # 视频长度，默认5秒
    
    if not prompt:
        return jsonify({'error': '请提供文字描述'}), 400
    
    print(f"文生视频请求: {prompt}, 风格: {style}")
    
    # 视频文件名和路径
    video_filename = f"{uuid.uuid4()}.mp4"
    video_path = os.path.join(GENERATED_VIDEOS, video_filename)
    
    # 风格处理词典
    style_prompts = {
        'realistic': ("高清真实照片风格", "High-definition realistic photo"),
        '3d': ("3D渲染效果", "3D rendering"),
        'animation': ("动画风格", "Animation style"),
        'artistic': ("艺术绘画风格", "Artistic painting")
    }
    
    # 获取风格前缀
    style_prefix = style_prompts.get(style, ('', ''))[0]
    enhanced_prompt = f"{style_prefix} - {prompt}"
    
    # 初始化客户端
    openai_client = None
    huggingface_client = None
    
    # 临时存储生成的帧
    temp_image_paths = []
    
    try:
        # 初始化OpenAI客户端(用于翻译)
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if openai_api_key:
            openai_client = OpenAI(api_key=openai_api_key)
    except Exception as e:
        print(f"OpenAI初始化错误: {str(e)}")
    
    try:
        # 初始化Hugging Face客户端(用于文生图)
        huggingface_api_key = os.environ.get('HUGGINGFACE_API_KEY')
        if huggingface_api_key:
            huggingface_client = InferenceClient(token=huggingface_api_key)
            print("成功初始化Hugging Face")
        else:
            print("未设置Hugging Face API密钥")
    except Exception as e:
        print(f"Hugging Face初始化错误: {str(e)}")
        huggingface_client = None
    
    # 确保目录存在
    os.makedirs(os.path.dirname(video_path), exist_ok=True)
    
    # 先尝试翻译中文提示词(如果存在)
    english_prompt = prompt
    has_chinese = any(u'\u4e00' <= char <= u'\u9fff' for char in prompt)
    
    if has_chinese and openai_client:
        try:
            # 如果有中文，翻译成英文提高兼容性
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a translator. Translate the Chinese text to English."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )
            english_prompt = response.choices[0].message.content.strip()
            print(f"翻译提示词: '{prompt}' -> '{english_prompt}'")
        except Exception as e:
            print(f"翻译错误: {str(e)}")
            # 添加风格前缀
            english_style = style_prompts.get(style, ('', ''))[1]
            english_prompt = f"{english_style} {prompt}"
    
    # 添加风格前缀到英文提示词
    english_style = style_prompts.get(style, ('', ''))[1]
    english_prompt = f"{english_style} {english_prompt}"
    print(f"最终提示词: {english_prompt}")
    
    # 生成帧的关键帧数量
    frame_count = 6  # 生成的关键帧数量
    
    # 为了创建不同角度和动作的关键帧
    motion_modifiers = [
        "at the beginning, stationary",
        "starting to move, first step",
        "in motion, action",
        "moving quickly, dynamic",
        "in full motion, peak action",
        "at the end position"
    ]
    
    print(f"开始生成 {frame_count} 个关键帧用于动画效果")
    
    # 开始生成关键帧
    for i in range(frame_count):
        try:
            if huggingface_client:
                # 使用Hugging Face生成关键帧
                motion_prompt = f"{english_prompt}, {motion_modifiers[i % len(motion_modifiers)]}"
                print(f"生成关键帧 {i+1}/{frame_count}: {motion_prompt}")
                
                # 调用文生图 API
                try:
                    image_bytes = huggingface_client.text_to_image(
                        prompt=motion_prompt,
                        model="stabilityai/stable-diffusion-xl-base-1.0",
                        negative_prompt="blurry, ugly, distorted, disfigured"
                    )
                    
                    # 保存生成的图像
                    temp_image_path = os.path.join(UPLOAD_FOLDER, f"frame_{i}_{uuid.uuid4()}.jpg")
                    
                    # 处理不同的返回类型
                    if hasattr(image_bytes, 'save'):
                        image_bytes.save(temp_image_path)
                    else:
                        with open(temp_image_path, 'wb') as f:
                            f.write(image_bytes)
                    
                    # 添加到关键帧列表
                    temp_image_paths.append(temp_image_path)
                    print(f"关键帧 {i+1} 生成成功")
                    
                except Exception as img_err:
                    print(f"关键帧 {i+1} 生成错误: {str(img_err)}")
                    # 出错时使用备用方法
                    fallback = True
            else:
                # 如果没有Hugging Face客户端，也使用备用方法
                print("没有Hugging Face客户端，使用备用方法")
                fallback = True
                
            # 备用方法：使用Picsum降级方案
            if 'fallback' in locals() and fallback:
                try:
                    # 使用固定种子确保一致帧
                    style_seed_base = {
                        'realistic': 1000,
                        '3d': 2000,
                        'animation': 3000,
                        'artistic': 4000
                    }.get(style, 1000)
                    
                    # 为每个播放生成随机种子，但每个帧使用不同的变化
                    collection_seed = random.randint(1, 9999)
                    frame_seed = style_seed_base + collection_seed + (i * 10)  # 每个帧稍有不同
                    
                    # 生成图像并保存
                    image_url = f"https://picsum.photos/seed/{frame_seed}/512/512"
                    temp_image_path = os.path.join(UPLOAD_FOLDER, f"fallback_{i}_{uuid.uuid4()}.jpg")
                    urllib.request.urlretrieve(image_url, temp_image_path)
                    temp_image_paths.append(temp_image_path)
                    print(f"备用图片 {i+1} 生成成功")
                except Exception as e:
                    print(f"备用图片 {i+1} 生成失败: {str(e)}")
        except Exception as e:
            print(f"关键帧生成错误: {str(e)}")
    
    # 检查是否成功生成了足够的帧
    print(f"生成了 {len(temp_image_paths)} 个关键帧")
    
    # 如果没有生成足够的帧，使用备用方案
    if len(temp_image_paths) < 2:
        print("关键帧数量不足，生成基本帧")
        for i in range(5):  # 生成至少5帧
            try:
                seed = 2000 + i * 100
                image_url = f"https://picsum.photos/seed/{seed}/512/512"
                temp_image_path = os.path.join(UPLOAD_FOLDER, f"basic_{i}_{uuid.uuid4()}.jpg")
                urllib.request.urlretrieve(image_url, temp_image_path)
                temp_image_paths.append(temp_image_path)
            except Exception as e:
                print(f"生成基本帧出错: {str(e)}")
                
    # 现在我们有了关键帧，开始创建视频
    try:
        # 检查是否有足够的关键帧
        if len(temp_image_paths) >= 2:
            print(f"开始使用{len(temp_image_paths)}个关键帧创建视频")
            
            # 初始化OpenCV视频写入器
            # 先检查第一帧尺寸
            first_frame = cv2.imread(temp_image_paths[0])
            if first_frame is None:
                print(f"无法读取关键帧：{temp_image_paths[0]}")
                frame_size = (512, 512)
            else:
                height, width, _ = first_frame.shape
                frame_size = (width, height)
            
            # 设置视频参数
            fps = 24
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            
            # 创建视频写入器
            print(f"创建视频：{video_path} 尺寸: {frame_size} fps: {fps}")
            video_writer = cv2.VideoWriter(video_path, fourcc, fps, frame_size)
            
            # 打开视频写入器成功检查
            if not video_writer.isOpened():
                print("视频写入器创建失败")
                raise Exception("视频写入器创建失败")
            
            # 为每两个关键帧之间生成帧间插值
            for i in range(len(temp_image_paths) - 1):
                # 加载当前帧和下一帧
                current_frame = cv2.imread(temp_image_paths[i])
                next_frame = cv2.imread(temp_image_paths[i+1])
                
                if current_frame is None or next_frame is None:
                    print(f"帧 {i} 或 {i+1} 无法读取，跳过")
                    continue
                
                # 确保尺寸一致
                if current_frame.shape != next_frame.shape:
                    next_frame = cv2.resize(next_frame, (current_frame.shape[1], current_frame.shape[0]))
                
                # 先添加当前帧几次
                hold_frames = int(fps * 0.5)  # 每个关键帧停电0.5秒
                for _ in range(hold_frames):
                    video_writer.write(current_frame)
                
                # 处理关键帧之间的过渡
                transition_frames = 12
                for j in range(transition_frames):
                    alpha = j / transition_frames
                    # 线性插值创建帧之间的平滑过渡
                    blended_frame = cv2.addWeighted(current_frame, 1-alpha, next_frame, alpha, 0)
                    video_writer.write(blended_frame)
            
            # 添加最后一帧并多停电1秒
            if len(temp_image_paths) > 0:
                last_frame = cv2.imread(temp_image_paths[-1])
                if last_frame is not None:
                    for _ in range(fps):
                        video_writer.write(last_frame)
            
            # 关闭视频写入器
            video_writer.release()
            print("视频生成成功")
            
            # 清理临时文件
            for img_path in temp_image_paths:
                try:
                    os.remove(img_path)
                except Exception as e:
                    print(f"无法删除临时文件 {img_path}: {str(e)}")
            
            # 返回视频URL
            return jsonify({
                'video': f"/static/generated/videos/{video_filename}",
                'prompt': prompt,
                'success': True,
                'method': 'keyframe-animation'
            })
        else:
            print("关键帧数量不足，无法创建视频")
            
    except Exception as e:
        print(f"创建视频错误: {traceback.format_exc()}")
    
    # 如果上面的方法失败，尝试使用基本的静态图像视频方法
    print("尝试使用基本的静态图像视频方法")
    
    # 1. 先尝试生成单帧图像作为基础
    try:
        base_image_result = text_to_image(prompt, style)
        base_image_path = base_image_result.get('image_path')
        if base_image_path and os.path.exists(base_image_path):
            print(f"成功生成基础图像: {base_image_path}")
            
            # 2. 初始化视频参数
            fps = 24
            duration = video_length  # 视频长度(秒)
            
            # 3. 读取基础图像并获取尺寸
            try:
                base_image = cv2.imread(base_image_path)
                if base_image is None:
                    raise Exception("无法读取基础图像")
                
                height, width, _ = base_image.shape
                frame_size = (width, height)
                
                # 4. 初始化视频写入器
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(video_path, fourcc, fps, frame_size)
                
                if not video_writer.isOpened():
                    raise Exception("无法创建视频写入器")
                
                # 5. 创建基本的缓慢变化效果
                total_frames = fps * duration
                
                # 创建缓慢的放大缩小/平移效果
                for i in range(int(total_frames)):
                    # 计算缩放比例，从1.0到最大1.05，然后再缩回
                    t = (i % (total_frames / 2)) / (total_frames / 2)
                    scale = 1.0 + 0.05 * math.sin(t * math.pi)
                    
                    # 计算平移量使图像微微浮动
                    shift_x = int(10 * math.sin(i * 0.05))
                    shift_y = int(5 * math.cos(i * 0.05))
                    
                    # 创建变换矩阵
                    M = cv2.getRotationMatrix2D((width/2, height/2), 0, scale)
                    M[0, 2] += shift_x
                    M[1, 2] += shift_y
                    
                    # 应用变换
                    transformed = cv2.warpAffine(base_image, M, (width, height))
                    
                    # 写入帧
                    video_writer.write(transformed)
                
                # 6. 完成视频生成
                video_writer.release()
                print(f"成功生成简单动画效果视频: {video_path}")
                
                # 7. 返回结果
                return jsonify({
                    'video': f"/static/generated/videos/{video_filename}",
                    'prompt': prompt,
                    'success': True,
                    'method': 'simple-animation'
                })
                
            except Exception as ve:
                print(f"创建视频错误: {str(ve)}")
                # 继续尝试下一个备用方法
        else:
            print("无法生成或找不到基础图像")
            
    except Exception as e:
        print(f"基本图像生成错误: {str(e)}")
    
    # 8. 最终备用方案：使用Picsum随机图像生成视频
    print("使用Picsum生成帧序列")
    
    try:
        # 生成多个图像帧
        frame_count = 5
        temp_image_paths = []
        
        # 为每个风格分配不同的基础种子
        style_seed_base = {
            'realistic': 1000,
            '3d': 2000,
            'animation': 3000,
            'artistic': 4000
        }.get(style, 1000)
        
        # 为整个序列生成一个随机种子
        collection_seed = random.randint(1, 9999)
        
        print(f"生成 {frame_count} 个视频帧")
        
        # 生成视频帧
        for i in range(frame_count):
            try:
                # 生成相关但略有变化的图像
                frame_seed = style_seed_base + collection_seed + (i * 10)
                image_url = f"https://picsum.photos/seed/{frame_seed}/512/512"
                
                # 保存到临时位置
                temp_image_path = os.path.join(UPLOAD_FOLDER, f"frame_{i}_{uuid.uuid4()}.jpg")
                urllib.request.urlretrieve(image_url, temp_image_path)
                temp_image_paths.append(temp_image_path)
                
                print(f"生成帧 {i+1}/{frame_count} 成功")
            except Exception as e:
                print(f"生成帧 {i+1} 出错: {str(e)}")
        
        # 检查是否有足够的帧
        if len(temp_image_paths) < 2:
            print("生成的帧数量不足，无法创建视频")
            return jsonify({
                'error': '生成视频帧失败',
                'prompt': prompt
            }), 500
        
        # 生成的帧已经足够，开始创建视频
        print(f"开始使用 {len(temp_image_paths)} 个帧创建最终视频")
        
        try:
            # 读取第一帧获取视频尺寸
            first_frame = cv2.imread(temp_image_paths[0])
            if first_frame is None:
                raise Exception("无法读取第一帧")
                
            height, width, _ = first_frame.shape
            frame_size = (width, height)
            
            # 设置视频参数
            fps = 24
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            
            # 创建视频写入器
            video_writer = cv2.VideoWriter(video_path, fourcc, fps, frame_size)
            
            # 插入帧并创建过渡效果
            for i in range(len(temp_image_paths)-1):
                # 加载当前帧和下一帧
                current_frame = cv2.imread(temp_image_paths[i])
                next_frame = cv2.imread(temp_image_paths[i+1])
                
                # 确保帧尺寸一致
                if current_frame.shape != next_frame.shape:
                    next_frame = cv2.resize(next_frame, (current_frame.shape[1], current_frame.shape[0]))
                
                # 添加当前帧停留效果
                hold_frames = int(fps * 0.7)  # 每帧停瀑0.7秒
                for _ in range(hold_frames):
                    video_writer.write(current_frame)
                
                # 创建过渡帧
                transition_frames = 10
                for j in range(transition_frames):
                    # 使用线性插值创建过渡
                    alpha = j / transition_frames
                    blended = cv2.addWeighted(current_frame, 1-alpha, next_frame, alpha, 0)
                    video_writer.write(blended)
            
            # 添加最后一帧的停留效果
            last_frame = cv2.imread(temp_image_paths[-1])
            if last_frame is not None:
                for _ in range(int(fps * 1.0)):  # 最后停电1秒
                    video_writer.write(last_frame)
            
            # 完成视频生成
            video_writer.release()
            print("视频生成成功")
            
            # 清理临时文件
            for img_path in temp_image_paths:
                try:
                    os.remove(img_path)
                except Exception as e:
                    print(f"清理临时文件错误: {str(e)}")
            
            # 返回结果
            return jsonify({
                'video': f"/static/generated/videos/{video_filename}",
                'prompt': prompt,
                'success': True,
                'method': 'picsum-animation'
            })
            
        except Exception as ve:
            print(f"创建视频错误: {str(ve)}")
    
    except Exception as e:
        print(f"最终备用视频生成错误: {str(e)}")
    
    # 如果所有方法都失败，返回错误
    print("所有视频生成方法均失败")
    return jsonify({
        'error': '生成视频失败，请稍后再试',
        'prompt': prompt
    }), 500
    
    # 所有方法均失败，返回错误
    # 所有方法均失败，返回错误
    print("所有视频生成方式均失败")
    return jsonify({
        'error': '生成视频失败，请稍后再试',
        'prompt': prompt
    }), 500

# 辅助函数：从图片创建视频
def create_video_from_image(image_path, output_path, effect='zoom', duration=5):
    try:
        img = cv2.imread(image_path)
        if img is None:
            return False
            
        height, width = img.shape[:2]
        fps = 30
        total_frames = fps * duration
        
        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # 根据效果创建不同的动画
        if effect == 'zoom':
            # 缩放效果
            for i in range(total_frames):
                scale = 1.0 + 0.3 * i / total_frames
                scaled_width = int(width * scale)
                scaled_height = int(height * scale)
                
                # 计算剪切区域以保持原始尺寸
                center_x, center_y = width // 2, height // 2
                x1 = max(0, center_x - width // 2)
                y1 = max(0, center_y - height // 2)
                
                # 调整大小然后剪切
                scaled_img = cv2.resize(img, (scaled_width, scaled_height))
                
                # 确保剪切区域在图像内
                if scaled_width > width and scaled_height > height:
                    crop_x = (scaled_width - width) // 2
                    crop_y = (scaled_height - height) // 2
                    cropped = scaled_img[crop_y:crop_y+height, crop_x:crop_x+width]
                    video.write(cropped)
                else:
                    # 如果缩放后太小，直接使用原图
                    video.write(img)
        
        elif effect == 'pan':
            # 平移效果
            for i in range(total_frames):
                progress = i / total_frames
                translation_x = int((width * 0.2) * progress)
                
                # 创建平移矩阵
                M = np.float32([[1, 0, translation_x], [0, 1, 0]])
                shifted = cv2.warpAffine(img, M, (width, height))
                video.write(shifted)
                
        elif effect == '3d':
            # 简单3D效果（透视变换）
            for i in range(total_frames):
                progress = i / total_frames
                # 透视变换的源点和目标点
                src_points = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
                dst_points = np.float32([
                    [width * 0.1 * progress, height * 0.1 * progress],
                    [width * (1 - 0.1 * progress), height * 0.1 * progress],
                    [0, height],
                    [width, height]
                ])
                
                # 计算透视变换矩阵
                M = cv2.getPerspectiveTransform(src_points, dst_points)
                warped = cv2.warpPerspective(img, M, (width, height))
                video.write(warped)
                
        else:  # 默认动画效果
            # 简单的淡入淡出效果
            for i in range(total_frames):
                alpha = 1.0
                if i < fps:  # 第一秒淡入
                    alpha = i / fps
                elif i > total_frames - fps:  # 最后一秒淡出
                    alpha = (total_frames - i) / fps
                
                # 应用透明度
                frame = cv2.addWeighted(img, alpha, np.zeros_like(img), 1-alpha, 0)
                video.write(frame)
        
        video.release()
        return True
    except Exception as e:
        print(f"视频创建失败：{e}")
        return False

# 辅助函数：从多张图像创建视频
def create_video_from_image_sequence(image_paths, output_path, duration=10):
    if not image_paths:
        print("没有提供图像路径")
        return False
        
    try:
        # 读取第一张图片设置视频宽高
        first_img = cv2.imread(image_paths[0])
        if first_img is None:
            return False
            
        height, width = first_img.shape[:2]
        fps = 30
        
        # 每个图像帧分配的时间和帧数
        frames_per_image = duration * fps / len(image_paths)
        transition_frames = min(int(fps * 0.5), int(frames_per_image * 0.3))  # 0.5秒过渡，最多为帧时间30%
        steady_frames = int(frames_per_image - transition_frames)
        
        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # 确保所有图像大小一致
        images = []
        for path in image_paths:
            img = cv2.imread(path)
            if img is None:
                continue
                
            # 调整大小以匹配第一帧
            if img.shape[:2] != (height, width):
                img = cv2.resize(img, (width, height))
            images.append(img)
            
        if not images:
            return False
            
        # 生成视频帧
        for i in range(len(images)):
            current_img = images[i]
            
            # 添加恢复帧
            for _ in range(steady_frames):
                video.write(current_img)
            
            # 添加过渡帧（除了最后一张图像）
            if i < len(images) - 1:
                next_img = images[i + 1]
                for j in range(transition_frames):
                    # 创建混合帧
                    alpha = j / transition_frames
                    blended = cv2.addWeighted(current_img, 1 - alpha, next_img, alpha, 0)
                    video.write(blended)
        
        # 关闭视频
        video.release()
        return True
        
    except Exception as e:
        print(f"从图像序列创建视频失败: {str(e)}")
        return False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
