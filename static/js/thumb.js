document.addEventListener("click", function(event) {
    const thumbnail = event.target.closest('.post_video_thumbnail, .reply_video_thumbnail');
    
    if (thumbnail) {
        thumbnail.style.display = "none";
        
        let video = null;

        // Primeiro tenta encontrar o container de post
        let container = thumbnail.closest('.post_image, .reply_image, .reply_img');
        
        if (container) {
            // Tenta encontrar o vídeo dentro do container
            video = container.querySelector('.post_video');
            
            if (!video) {
                // Se não encontrar, tenta subir mais na hierarquia
                container = container.parentElement;
                if (container) {
                    video = container.querySelector('.post_video');
                }
            }
        }

        if (video) {
            video.style.display = "block";
            video.style.maxWidth = "100%";
            video.style.maxHeight = "100%";
            video.play().catch(e => console.log("Erro ao reproduzir vídeo:", e));
        } else {
            console.warn("Elemento de vídeo não encontrado para a thumbnail", thumbnail);
        }
    }
});
