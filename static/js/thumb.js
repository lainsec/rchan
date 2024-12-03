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
document.addEventListener('DOMContentLoaded', function() {
    const videos = document.querySelectorAll('.video');
    const canvases = document.querySelectorAll('.video-thumbnail');
    const videoPlayers = document.querySelectorAll('.post_video');
    
    videos.forEach(function(video, index) {
      const canvas = canvases[index]; 
      const videoPlayer = videoPlayers[index]; 

      video.addEventListener('loadeddata', function() {
        video.currentTime = 1;
      });
      video.addEventListener('seeked', function() {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height); 
      });
  
      canvas.addEventListener('click', function() {
        canvas.style.display = 'none'; 
        videoPlayer.style.display = 'block';  
        videoPlayer.play(); 
      });
    });
});
