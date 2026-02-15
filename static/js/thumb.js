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

            // Adicionar botão de fechar se não existir
            let infoContainer = container.querySelector('.post_image_info, .reply_image_info');
            if (infoContainer && !infoContainer.querySelector('.video-close-btn')) {
                const closeBtn = document.createElement('a');
                closeBtn.href = "javascript:void(0)";
                closeBtn.className = "video-close-btn";
                closeBtn.textContent = " (close)";
                closeBtn.style.marginLeft = "5px";
                
                closeBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    // Parar e esconder vídeo
                    video.pause();
                    video.style.display = "none";
                    // Mostrar thumbnail
                    thumbnail.style.display = "";
                    // Remover botão close
                    closeBtn.remove();
                });

                infoContainer.appendChild(closeBtn);
            }
        } else {
            console.warn("Elemento de vídeo não encontrado para a thumbnail", thumbnail);
        }
    }
});
