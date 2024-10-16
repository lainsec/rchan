const video = document.getElementById('lastpost_video');
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  video.addEventListener('loadedmetadata', function() {
    video.currentTime = 2;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageData = canvas.toDataURL();

    const img = document.createElement('img');
    img.src = imageData;

    canvas.remove();
});
