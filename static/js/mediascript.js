document.addEventListener('click', function(event) {
    // Verifica se o clique foi em uma imagem que deve ser expandida
    const img = event.target.closest('.post_img, .reply_img');
    
    // Se não for uma imagem válida ou for uma thumbnail de vídeo, ignora
    if (!img || img.id === "post_video_thumbnail" || img.classList.contains('post_video_thumbnail') || img.classList.contains('reply_video_thumbnail')) {
        return;
    }

    // Esconde a imagem original
    img.style.display = 'none';

    // Cria a versão expandida
    const expandedImg = document.createElement('img');
    expandedImg.classList.add(img.classList.contains('post_img') ? 'post_img_resized' : 'reply_img_resized');
    expandedImg.src = img.src;
    expandedImg.alt = img.alt;
    expandedImg.style.cursor = 'pointer';
    expandedImg.style.maxWidth = "100%";

    // Insere após a imagem original
    img.parentNode.insertBefore(expandedImg, img.nextSibling);

    // Adiciona evento para fechar a imagem expandida
    expandedImg.addEventListener('click', function(e) {
        e.stopPropagation(); // Evita que o evento se propague
        this.remove();
        img.style.display = '';
    });
});
