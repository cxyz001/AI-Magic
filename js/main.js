/**
 * AI Magic - Main JavaScript File
 * Handles core functionality for the application
 */

// DOM Elements
// Tab navigation
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Text to image elements
const textToImageInput = document.getElementById('text-to-image-input');
const imageStyleSelect = document.getElementById('image-style');
const generateImageBtn = document.getElementById('generate-image-btn');
const imageLoadingIndicator = document.getElementById('image-loading');
const imageResults = document.getElementById('image-results');
const downloadAllImagesBtn = document.getElementById('download-all-images');

// Image to video elements
const imageUploadArea = document.getElementById('image-upload-area');
const imageUploadInput = document.getElementById('image-upload');
const selectImageBtn = document.getElementById('select-image-btn');
const uploadedImagePreview = document.getElementById('uploaded-image-preview');
const uploadedImageElement = document.querySelector('#uploaded-image-preview img');
const changeImageBtn = document.getElementById('change-image-btn');
const videoEffectSelect = document.getElementById('video-effect');
const videoLengthSelect = document.getElementById('video-length');
const generateVideoFromImageBtn = document.getElementById('generate-video-from-image-btn');
const videoFromImageLoadingIndicator = document.getElementById('video-from-image-loading');
const videoFromImageResult = document.getElementById('video-from-image-result');
const videoFromImageElement = document.querySelector('#video-from-image-result video');
const downloadVideoFromImageBtn = document.getElementById('download-video-from-image');
const videoFromImageFormatSelect = document.getElementById('video-from-image-format');

// Text to video elements
const textToVideoInput = document.getElementById('text-to-video-input');
const videoStyleSelect = document.getElementById('video-style');
const textToVideoLengthSelect = document.getElementById('text-to-video-length');
const generateVideoFromTextBtn = document.getElementById('generate-video-from-text-btn');
const videoFromTextLoadingIndicator = document.getElementById('video-from-text-loading');
const videoFromTextResult = document.getElementById('video-from-text-result');
const videoFromTextElement = document.querySelector('#video-from-text-result video');
const downloadVideoFromTextBtn = document.getElementById('download-video-from-text');
const videoFromTextFormatSelect = document.getElementById('video-from-text-format');

// Modal elements
const aboutLink = document.getElementById('about-link');
const helpLink = document.getElementById('help-link');
const aboutModal = document.getElementById('about-modal');
const helpModal = document.getElementById('help-modal');
const closeModalButtons = document.querySelectorAll('.close-modal');

// Tab Navigation
tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Remove active class from all buttons and contents
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabContents.forEach(content => content.classList.remove('active'));
        
        // Add active class to clicked button and corresponding content
        button.classList.add('active');
        const tabId = button.getAttribute('data-tab');
        document.getElementById(tabId).classList.add('active');
    });
});

// TEXT TO IMAGE FUNCTIONALITY
generateImageBtn.addEventListener('click', async () => {
    const prompt = textToImageInput.value.trim();
    const style = imageStyleSelect.value;
    
    if (!prompt) {
        alert('请输入图像描述');
        return;
    }
    
    // Show loading, hide results
    imageResults.classList.add('hidden');
    imageLoadingIndicator.classList.remove('hidden');
    
    try {
        // Call the API service
        const imageUrls = await ApiService.generateImagesFromText(prompt, style);
        
        // Update image elements
        const imageElements = document.querySelectorAll('#image-results .result-item img');
        const downloadButtons = document.querySelectorAll('#image-results .result-item .download-btn');
        
        imageElements.forEach((img, index) => {
            if (imageUrls[index]) {
                // 获取完整URL（添加API基础路径）
                const fullUrl = ApiService.getFullUrl(imageUrls[index]);
                img.src = fullUrl;
                img.setAttribute('data-original-url', fullUrl);
                
                // Setup download button
                downloadButtons[index].onclick = () => {
                    const filename = `AI_Magic_Image_${index+1}.jpg`;
                    downloadImage(fullUrl, filename);
                };
            }
        });
        
        // Setup download all button
        downloadAllImagesBtn.onclick = () => {
            imageUrls.forEach((url, index) => {
                setTimeout(() => {
                    const filename = `AI_Magic_Image_${index+1}.jpg`;
                    downloadImage(ApiService.getFullUrl(url), filename);
                }, index * 500); // Stagger downloads
            });
        };
        
        // Hide loading and show results
        imageLoadingIndicator.classList.add('hidden');
        imageResults.classList.remove('hidden');
        
    } catch (error) {
        console.error('生成图片失败:', error);
        alert(`生成图片失败: ${error.message || '未知错误'}`);
        imageLoadingIndicator.classList.add('hidden');
    }
});

// IMAGE TO VIDEO FUNCTIONALITY
// Handle file selection
selectImageBtn.addEventListener('click', () => {
    imageUploadInput.click();
});

// Handle drag and drop area
imageUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    imageUploadArea.classList.add('active');
});

imageUploadArea.addEventListener('dragleave', () => {
    imageUploadArea.classList.remove('active');
});

imageUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    imageUploadArea.classList.remove('active');
    
    if (e.dataTransfer.files.length) {
        handleImageUpload(e.dataTransfer.files[0]);
    }
});

// Handle file input change
imageUploadInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleImageUpload(e.target.files[0]);
    }
});

// Change image button
changeImageBtn.addEventListener('click', () => {
    uploadedImagePreview.classList.add('hidden');
    imageUploadArea.classList.remove('hidden');
    generateVideoFromImageBtn.disabled = true;
});

function handleImageUpload(file) {
    // Check if file is an image
    if (!file.type.startsWith('image/')) {
        alert('请上传图片文件');
        return;
    }
    
    // Check file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert('图片大小不能超过5MB');
        return;
    }
    
    const reader = new FileReader();
    
    reader.onload = (e) => {
        // Display the uploaded image
        uploadedImageElement.src = e.target.result;
        
        // Show the image preview and hide the upload area
        imageUploadArea.classList.add('hidden');
        uploadedImagePreview.classList.remove('hidden');
        
        // Enable the generate video button
        generateVideoFromImageBtn.disabled = false;
    };
    
    reader.readAsDataURL(file);
}

// Generate video from image
generateVideoFromImageBtn.addEventListener('click', async () => {
    // 我们需要使用上传的文件，而不是图片数据
    const uploadedImageFile = imageUploadInput.files[0];
    const effect = videoEffectSelect.value;
    const length = parseInt(videoLengthSelect.value);
    
    if (!uploadedImageFile) {
        alert('请先上传图片');
        return;
    }
    
    // Show loading, hide results
    videoFromImageResult.classList.add('hidden');
    videoFromImageLoadingIndicator.classList.remove('hidden');
    
    // Setup progress simulation
    const progressBar = videoFromImageLoadingIndicator.querySelector('.progress');
    const progressText = videoFromImageLoadingIndicator.querySelector('.progress-text');
    simulateProgress(progressBar, progressText);
    
    try {
        // Call the API service
        const videoUrl = await ApiService.generateVideoFromImage(uploadedImageFile, effect, length);
        
        // Update video element with full URL
        const fullVideoUrl = ApiService.getFullUrl(videoUrl);
        videoFromImageElement.src = fullVideoUrl;
        videoFromImageElement.load(); // Reload video with new source
        
        // Setup download button
        downloadVideoFromImageBtn.onclick = () => {
            const format = videoFromImageFormatSelect.value;
            const filename = `AI_Magic_Video.${format}`;
            downloadVideo(fullVideoUrl, filename);
        };
        
        // Hide loading and show results
        videoFromImageLoadingIndicator.classList.add('hidden');
        videoFromImageResult.classList.remove('hidden');
        
    } catch (error) {
        console.error('生成视频失败:', error);
        alert(`生成视频失败: ${error.message || '未知错误'}`);
        videoFromImageLoadingIndicator.classList.add('hidden');
    }
});

// TEXT TO VIDEO FUNCTIONALITY
generateVideoFromTextBtn.addEventListener('click', async () => {
    const prompt = textToVideoInput.value.trim();
    const style = videoStyleSelect.value;
    const length = parseInt(textToVideoLengthSelect.value);
    
    if (!prompt) {
        alert('请输入视频描述');
        return;
    }
    
    // Show loading, hide results
    videoFromTextResult.classList.add('hidden');
    videoFromTextLoadingIndicator.classList.remove('hidden');
    
    // Setup progress simulation
    const progressBar = videoFromTextLoadingIndicator.querySelector('.progress');
    const progressText = videoFromTextLoadingIndicator.querySelector('.progress-text');
    simulateProgress(progressBar, progressText, 5); // Slower progress for text-to-video
    
    try {
        // Call the API service
        const videoUrl = await ApiService.generateVideoFromText(prompt, style, length);
        
        // Update video element with full URL
        const fullVideoUrl = ApiService.getFullUrl(videoUrl);
        videoFromTextElement.src = fullVideoUrl;
        videoFromTextElement.load(); // Reload video with new source
        
        // Setup download button
        downloadVideoFromTextBtn.onclick = () => {
            const format = videoFromTextFormatSelect.value;
            const filename = `AI_Magic_Video_${style}.${format}`;
            downloadVideo(fullVideoUrl, filename);
        };
        
        // Hide loading and show results
        videoFromTextLoadingIndicator.classList.add('hidden');
        videoFromTextResult.classList.remove('hidden');
        
    } catch (error) {
        console.error('生成视频失败:', error);
        alert(`生成视频失败: ${error.message || '未知错误'}`);
        videoFromTextLoadingIndicator.classList.add('hidden');
    }
});

// MODAL FUNCTIONALITY
aboutLink.addEventListener('click', (e) => {
    e.preventDefault();
    aboutModal.classList.add('active');
});

helpLink.addEventListener('click', (e) => {
    e.preventDefault();
    helpModal.classList.add('active');
});

closeModalButtons.forEach(button => {
    button.addEventListener('click', () => {
        aboutModal.classList.remove('active');
        helpModal.classList.remove('active');
    });
});

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target === aboutModal) {
        aboutModal.classList.remove('active');
    }
    if (e.target === helpModal) {
        helpModal.classList.remove('active');
    }
});

// UTILITY FUNCTIONS
function downloadImage(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function downloadVideo(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function simulateProgress(progressBar, progressText, speed = 10, etaElement = null) {
    let progress = 0;
    const interval = setInterval(() => {
        progress += 1;
        
        if (progress > 99) {
            clearInterval(interval);
            progress = 100;
        }
        
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${progress}%`;
        
        if (etaElement) {
            const remainingProgress = 100 - progress;
            const remainingSeconds = Math.round(remainingProgress * speed / 10);
            const minutes = Math.floor(remainingSeconds / 60);
            const seconds = remainingSeconds % 60;
            
            if (minutes > 0) {
                etaElement.textContent = `预计完成时间: 约${minutes}分${seconds}秒`;
            } else if (seconds > 0) {
                etaElement.textContent = `预计完成时间: 约${seconds}秒`;
            } else {
                etaElement.textContent = `处理即将完成...`;
            }
        }
    }, speed * 10);
}
