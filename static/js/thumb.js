document.addEventListener("DOMContentLoaded", function() {
  const thumbnails = document.querySelectorAll("#post_video_thumbnail");

  thumbnails.forEach(thumbnail => {
      thumbnail.addEventListener("click", function() {
          thumbnail.style.display = "none";

          
          const video = thumbnail.nextElementSibling;

          if (video && video.classList.contains("post_video")) {
              video.style.display = "block";
          }
      });
  });
});
