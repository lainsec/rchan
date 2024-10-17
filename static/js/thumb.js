const videos = document.querySelectorAll('video'); 

videos.forEach(video => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    video.addEventListener('loadedmetadata', function() {
        video.currentTime = 2; 

        video.addEventListener('seeked', function() {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            const imageData = canvas.toDataURL();

            const thumbnailVideo = document.getElementById('thumbnail_video');
            thumbnailVideo.setAttribute('poster', imageData);

            canvas.remove();
        });
    });
});
