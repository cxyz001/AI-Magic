/**
 * AI Magic - Mock API Service
 * Simulates API responses for demonstration purposes
 */

// Mock API Service
const apiService = {
    // Text to Image API
    generateImagesFromText: async (prompt, style) => {
        console.log(`Generating images with prompt: ${prompt}, style: ${style}`);
        
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // 使用固定图片URL替代Unsplash随机服务
        // 根据选择的风格提供不同的图片
        const styleImages = {
            'realistic': [
                'https://picsum.photos/800/600?random=1',
                'https://picsum.photos/800/600?random=2',
                'https://picsum.photos/800/600?random=3',
                'https://picsum.photos/800/600?random=4'
            ],
            'cartoon': [
                'https://picsum.photos/800/600?random=5',
                'https://picsum.photos/800/600?random=6',
                'https://picsum.photos/800/600?random=7',
                'https://picsum.photos/800/600?random=8'
            ],
            'painting': [
                'https://picsum.photos/800/600?random=9',
                'https://picsum.photos/800/600?random=10',
                'https://picsum.photos/800/600?random=11',
                'https://picsum.photos/800/600?random=12'
            ],
            'sketch': [
                'https://picsum.photos/800/600?random=13',
                'https://picsum.photos/800/600?random=14',
                'https://picsum.photos/800/600?random=15',
                'https://picsum.photos/800/600?random=16'
            ],
            'anime': [
                'https://picsum.photos/800/600?random=17',
                'https://picsum.photos/800/600?random=18',
                'https://picsum.photos/800/600?random=19',
                'https://picsum.photos/800/600?random=20'
            ]
        };
        
        // 获取对应风格的图片，如果风格不存在则使用realistic风格
        const placeholders = styleImages[style] || styleImages['realistic'];
        
        // 添加时间戳参数避免图片缓存问题
        const timestamp = new Date().getTime();
        return placeholders.map(url => `${url}&t=${timestamp}`);
    },
    
    // Image to Video API
    generateVideoFromImage: async (imageData, effect, length) => {
        console.log(`Generating video from image with effect: ${effect}, length: ${length}s`);
        
        // Simulate API delay (longer for video generation)
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        // In a real application, this would call a real AI service
        // For this demo, we return a placeholder video
        // Placeholder video options based on the effect
        const videoOptions = {
            'zoom': 'https://assets.mixkit.co/videos/preview/mixkit-trees-in-the-forest-by-a-small-canal-1884-large.mp4',
            'pan': 'https://assets.mixkit.co/videos/preview/mixkit-clouds-and-blue-sky-2408-large.mp4',
            '3d': 'https://assets.mixkit.co/videos/preview/mixkit-white-sand-beach-and-palm-trees-1564-large.mp4',
            'animate': 'https://assets.mixkit.co/videos/preview/mixkit-woman-running-above-the-city-1172-large.mp4'
        };
        
        return videoOptions[effect] || videoOptions['zoom'];
    },
    
    // Text to Video API
    generateVideoFromText: async (prompt, style, length) => {
        console.log(`Generating video from text: ${prompt}, style: ${style}, length: ${length}s`);
        
        // Simulate API delay (longest for text-to-video)
        await new Promise(resolve => setTimeout(resolve, 8000));
        
        // In a real application, this would call a real AI service
        // For this demo, we return a placeholder video based on style
        const videoOptions = {
            'realistic': 'https://assets.mixkit.co/videos/preview/mixkit-aerial-view-of-city-traffic-at-night-4584-large.mp4',
            'cinematic': 'https://assets.mixkit.co/videos/preview/mixkit-stars-in-space-1610-large.mp4',
            'cartoon': 'https://assets.mixkit.co/videos/preview/mixkit-animation-of-futuristic-devices-99786-large.mp4',
            'anime': 'https://assets.mixkit.co/videos/preview/mixkit-digital-animation-of-a-city-4662-large.mp4'
        };
        
        return videoOptions[style] || videoOptions['cinematic'];
    }
};

// Log that API service is ready
console.log('AI Magic Mock API Service initialized');
