// AI Magic - API Service
// 与后端API通信的服务

const API_BASE_URL = 'http://localhost:5000';

const ApiService = {
    /**
     * 文生图 API - 从文本描述生成图像
     * @param {string} prompt - 文本描述
     * @param {string} style - 图像风格 (realistic, cartoon, painting, sketch, anime)
     * @returns {Promise} 包含图像URL数组的Promise
     */
    generateImagesFromText: async (prompt, style) => {
        try {
            console.log(`[API] 文生图请求: 提示词="${prompt}", 风格=${style}`);
            
            const response = await fetch(`${API_BASE_URL}/api/text-to-image`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt, style })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || '图像生成失败');
            }
            
            const data = await response.json();
            console.log('[API] 文生图响应:', data);
            return data.images;
        } catch (error) {
            console.error('[API] 文生图错误:', error);
            throw error;
        }
    },
    
    /**
     * 图生视频 API - 从上传的图片生成视频
     * @param {File} imageFile - 上传的图片文件
     * @param {string} effect - 视频效果 (zoom, pan, 3d, animate)
     * @param {number} length - 视频长度（秒）
     * @returns {Promise} 包含视频URL的Promise
     */
    generateVideoFromImage: async (imageFile, effect, length) => {
        try {
            console.log(`[API] 图生视频请求: 效果=${effect}, 长度=${length}秒`);
            
            const formData = new FormData();
            formData.append('image', imageFile);
            formData.append('effect', effect);
            formData.append('length', length);
            
            const response = await fetch(`${API_BASE_URL}/api/image-to-video`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || '视频生成失败');
            }
            
            const data = await response.json();
            console.log('[API] 图生视频响应:', data);
            return data.video;
        } catch (error) {
            console.error('[API] 图生视频错误:', error);
            throw error;
        }
    },
    
    /**
     * 文生视频 API - 从文本描述生成视频
     * @param {string} prompt - 视频描述
     * @param {string} style - 视频风格 (realistic, 3d, animation, artistic)
     * @param {number} length - 视频长度（秒）
     * @returns {Promise} 包含视频URL的Promise
     */
    generateVideoFromText: async (prompt, style, length) => {
        try {
            console.log(`[API] 文生视频请求: 提示词="${prompt}", 风格=${style}, 长度=${length}秒`);
            
            const response = await fetch(`${API_BASE_URL}/api/text-to-video`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt, style, length })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || '视频生成失败');
            }
            
            const data = await response.json();
            console.log('[API] 文生视频响应:', data);
            return data.video;
        } catch (error) {
            console.error('[API] 文生视频错误:', error);
            throw error;
        }
    },

    /**
     * 构建完整URL (将相对路径转换为绝对URL)
     * @param {string} path - 相对路径
     * @returns {string} 完整的URL
     */
    getFullUrl: (path) => {
        if (path.startsWith('http')) {
            return path;
        }
        return `${API_BASE_URL}${path}`;
    }
};

// 导出API服务
window.ApiService = ApiService;
