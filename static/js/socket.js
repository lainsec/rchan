var jQuery = jQuery.noConflict();
var socket = io();

const notification_path = '/static/audios/notification.mp3';
const notification = new Audio(notification_path);
let originalTitle = document.title;
let unseenCount = 0;
function updateTitle() {
    if (unseenCount > 0) {
        document.title = `(${unseenCount}) ${originalTitle}`;
    } else {
        document.title = originalTitle;
    }
}
function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    const vh = window.innerHeight || document.documentElement.clientHeight;
    return rect.top < vh && rect.bottom > 0;
}
const unseenObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const el = entry.target;
            if (el.classList.contains('unseen')) {
                el.classList.remove('unseen');
                unseenCount = Math.max(0, unseenCount - 1);
                updateTitle();
            }
            unseenObserver.unobserve(el);
        }
    });
}, { threshold: 0.5 });
function markUnseenById(id) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!el.classList.contains('unseen')) {
        el.classList.add('unseen');
        unseenCount += 1;
        updateTitle();
        unseenObserver.observe(el);
    }
}

function getCurrentBoard() {
    const path = window.location.pathname;
    const segments = path.replace(/^\//, '').split('/');
    return segments[0] || '';
}

socket.on('move_post', function(data) {
    const postId = data.post.id;
    const postElement = document.getElementById(postId);
    
    if (postElement) {
        // Aplica o estilo de opacidade 50%
        postElement.style.opacity = '0.5';
        postElement.style.transition = 'opacity 0.3s ease';
        
        // Adiciona uma marcação visual indicando que foi movido
        const deletedMarker = document.createElement('div');
        deletedMarker.textContent = `[POST MOVED → /${data.post.new_board}/]`;
        deletedMarker.style.color = '#ff4444';
        deletedMarker.style.fontWeight = 'bold';
        deletedMarker.style.marginLeft = '10px';
        deletedMarker.style.display = 'inline-block';
        
        // Encontra o cabeçalho do post para inserir a marcação
        const postHeader = postElement.querySelector('.postInfo') || 
                          postElement.querySelector('.reply-postInfo');
        
        if (postHeader) {
            postHeader.appendChild(deletedMarker);
        } else {
            postElement.appendChild(deletedMarker);
        }
        
        // Opcional: apenas impedir novas respostas/ações, mas permitir seleção de texto
        postElement.classList.add('moved-post');
        
    } else {
        console.log(`Post ${postId} não encontrado na página`);
    }
});


socket.on('delete_post', function(data) {
    const postId = data.post.id;
    const postElement = document.getElementById(postId);
    
    if (postElement) {
        // Aplica o estilo de opacidade 50%
        postElement.style.opacity = '0.5';
        postElement.style.transition = 'opacity 0.3s ease';
        
        // Adiciona uma marcação visual indicando que foi deletado
        const deletedMarker = document.createElement('div');
        deletedMarker.textContent = '[BALEETED]';
        deletedMarker.style.color = '#ff4444';
        deletedMarker.style.fontWeight = 'bold';
        deletedMarker.style.marginLeft = '10px';
        
        // Encontra o cabeçalho do post para inserir a marcação
        const postHeader = postElement.querySelector('.postInfo') || 
                          postElement.querySelector('.reply-postInfo');
        
        if (postHeader) {
            postHeader.appendChild(deletedMarker);
        }
        
        // Opcional: Desabilita interações com o post deletado
        postElement.style.pointerEvents = 'none';
        
    } else {
        console.log(`Post ${postId} não encontrado na página`);
    }
});

socket.on('ban_post', function(data) {
    const postId = data.post.id;
    const postElement = document.getElementById(postId);
    
    if (postElement) {
        // Aplica o estilo de opacidade 50%
        postElement.style.opacity = '0.5';
        postElement.style.transition = 'opacity 0.3s ease';
        
        // Adiciona uma marcação visual indicando que foi deletado
        const deletedMarker = document.createElement('div');
        deletedMarker.textContent = '[The user has banned from this thread]';
        deletedMarker.style.color = '#ff4444';
        deletedMarker.style.fontWeight = 'bold';
        deletedMarker.style.marginLeft = '10px';
        
        // Encontra o cabeçalho do post para inserir a marcação
        const postHeader = postElement.querySelector('.postInfo') || 
                          postElement.querySelector('.reply-postInfo');
        
        if (postHeader) {
            postHeader.appendChild(deletedMarker);
        }
        
        // Opcional: Desabilita interações com o post deletado
        postElement.style.pointerEvents = 'none';
        
    }
});

socket.on('nova_postagem', function(data) {
    const currentBoard = getCurrentBoard();
    const isSameBoard = currentBoard === data.post.board;
    const currentPath = window.location.pathname;
    
    if (isSameBoard) {
        notification.play();
    }
    
    if (isSameBoard) {
        if (data.type === 'New Thread') {
            if (currentPath === `/${currentBoard}` || currentPath === `/${currentBoard}/`) {
                addNewThread(data.post);
                markUnseenById(data.post.id);
            }
        } else if (data.type === 'New Reply') {
            // Verifica se o thread pai existe na página atual
            const parentThread = document.getElementById(data.post.thread_id);
            if (parentThread) {
                addNewReply(data.post);
                markUnseenById(data.post.id);
            }
        }
    }
});

function addNewThread(post) {
    // Use default name if empty
    const displayName = post.name === '' ? 'ドワーフ' : post.name;
    
    const threadHTML = `
        <div class="divisoria"></div>
        <div class="post" post-role="${post.role}" id="${post.id}" bis_skin_checked="1">
            <div class="postInfo" bis_skin_checked="1">
                <input id="togglemodoptions" type="checkbox" class="deletionCheckBox" name="${post.id}" form="banDeleteForm">
                <span class="nameBlock"><span class="name">${displayName}</span></span>
                <span class="postDate" data-original-date="${post.date}" title="${post.date}">agora mesmo</span>
                <a href="/${post.board}/thread/${post.id}" class="postLink" bis_skin_checked="1">No. </a> 
                <a class="postLink" href="/${post.board}/thread/${post.id}" bis_skin_checked="1">${post.id}</a>
                <a class="postLink" href="/${post.board}/thread/${post.id}" bis_skin_checked="1"> [Replies]</a>
                <div id="threadmodoptions" class="mod-options" style="display: none; gap: 1em; padding-left: 1em;" bis_skin_checked="1">
                    <!-- ... rest of the thread HTML ... -->
                </div>
            </div>
            <div class="post_content_container" bis_skin_checked="1">
                ${post.files ? generateFilesHTML(post.files, 'post', post.media_approved, post.id) : ''}
                <div class="post_content" bis_skin_checked="1">
                    <pre>${post.content}</pre>
                </div>
                <div class="replies" bis_skin_checked="1"></div>
            </div>
        </div>
    `;
    
    document.getElementById('posts_board').insertAdjacentHTML('afterbegin', threadHTML);
}

function addNewReply(reply) {
    // Use default name if empty
    const displayName = reply.name === '' ? 'ドワーフ' : reply.name;
    
    const replyHTML = `
        <div class="reply" id="${reply.id}" bis_skin_checked="1">
            <div class="reply-postInfo" bis_skin_checked="1">
                <input id="togglemodoptions" type="checkbox" class="deletionCheckBox" name="${reply.id}" form="banDeleteForm">
                <span class="nameBlock"><span class="name">${displayName}</span></span>
                <span class="postDate" data-original-date="${reply.date}" title="${reply.date}">agora mesmo</span>
                <a href="/${reply.board}/thread/${reply.thread_id}" class="postLink" bis_skin_checked="1">No. </a> 
                <a class="postLink" href="/${reply.board}/thread/${reply.thread_id}#${reply.id}" onclick="quotePostId(${reply.id})" bis_skin_checked="1">${reply.id}</a>
                <div id="threadmodoptions" class="mod-options" style="display: none; gap: 1em;" bis_skin_checked="1">
                    <form action="/delete_reply/${reply.id}" method="post">
                        <input type="hidden" name="board_owner" value="${reply.board}">
                        <button style="background-color:transparent; border: none; cursor: pointer;" type="submit">
                            <i class="fa-solid fa-trash" style="color: var(--cor-texto);"></i>
                        </button>
                    </form>
                </div>
            </div>
            <div class="post_content_container" bis_skin_checked="1">
                ${reply.files ? generateFilesHTML(reply.files, 'reply', reply.media_approved, reply.id) : ''}
                <div class="reply_content" bis_skin_checked="1">
                    <pre>${reply.content}</pre>
                </div>
            </div>
        </div>
    `;
    
    const repliesContainer = document.querySelector(`div.post[id="${reply.thread_id}"] .replies`) || 
                            document.querySelector(`#${reply.thread_id} .replies`);
    
    if (repliesContainer) {
        repliesContainer.insertAdjacentHTML('beforeend', replyHTML);
        
        // Verifica se não estamos na página do thread específico
        const isThreadPage = window.location.pathname.match(/\/[^\/]+\/thread\/\d+/);
        if (!isThreadPage) {
            // Move o thread para o topo da lista de posts
            const parentThread = document.getElementById(reply.thread_id);
            if (parentThread) {
                const postsBoard = document.getElementById('posts_board');
                postsBoard.insertBefore(parentThread, postsBoard.firstChild);
            }
        }
    }
}

function generateFilesHTML(files, type, media_approved, postId) {
    if (media_approved === 0) {
        return `<div class="post_files" bis_skin_checked="1">
                    <div class="${type === 'post' ? 'post_image' : 'reply_image'}" style="text-align: center; padding: 10px; border: 1px dashed #666; background: rgba(0,0,0,0.1);">
                        <img src="/static/imgs/decoration/mediapendingapproval.png">
                    </div>
                </div>`;
    }

    let html = '<div class="post_files" bis_skin_checked="1">';
    
    files.forEach(file => {
        const isImage = /\.(jpeg|jpg|gif|png|webp)$/i.test(file);
        const isVideo = /\.(mp4|mov|webm)$/i.test(file);
        const isYoutube = file.startsWith('youtube:');
        const folder = type === 'post' ? 'post_images' : 'reply_images';
        const thumbFolder = folder + '/thumbs';
        const baseName = file.split('.').slice(0, -1).join('.');
        const extension = file.split('.').pop();
        
        // Shorten filename to 17 chars + extension
        const displayName = baseName.length > 17 
            ? `${baseName.substring(0, 17)}...${extension}`
            : `${baseName}.${extension}`;

        if (isYoutube) {
            const videoId = file.split(':')[1];
            if (type === 'post') {
                html += `
                    <div class="post_image" bis_skin_checked="1">
                        <div class="post_image_info" bis_skin_checked="1">
                            <a class="image_url" href="https://youtu.be/${videoId}" target="_blank">
                                YouTube Embed
                            </a>
                        </div>
                        <img class="post_img post_video_thumbnail" 
                             src="https://img.youtube.com/vi/${videoId}/0.jpg"
                             onclick="var iframe = document.createElement('iframe'); iframe.src = 'https://www.youtube.com/embed/${videoId}?autoplay=1'; iframe.width = '100%'; iframe.height = '240'; iframe.frameBorder = '0'; iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture'; iframe.allowFullscreen = true; this.parentNode.replaceChild(iframe, this); return false;"
                             style="cursor: pointer;">
                    </div>
                `;
            } else {
                html += `
                    <div class="reply_image" bis_skin_checked="1">
                        <div class="reply_image_info" bis_skin_checked="1">
                             <a class="image_url" href="https://youtu.be/${videoId}" target="_blank">
                                YouTube Embed
                            </a>
                        </div>
                        <img class="reply_img post_video_thumbnail" 
                             src="https://img.youtube.com/vi/${videoId}/0.jpg"
                             onclick="var iframe = document.createElement('iframe'); iframe.src = 'https://www.youtube.com/embed/${videoId}?autoplay=1'; iframe.width = '100%'; iframe.height = '240'; iframe.frameBorder = '0'; iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture'; iframe.allowFullscreen = true; this.parentNode.replaceChild(iframe, this); return false;"
                             style="cursor: pointer;">
                    </div>
                `;
            }
        } else if (isImage) {
            html += `
                <div class="${type === 'post' ? 'post_image' : 'reply_image'}" bis_skin_checked="1">
                    <div class="post_image_info" bis_skin_checked="1">
                        <a class="image_url" href="/static/${folder}/${file}" bis_skin_checked="1">
                            ${displayName}
                        </a>
                    </div>
                    <img draggable="false" class="${type === 'post' ? 'post_img' : 'reply_img'}" src="/static/${folder}/${file}" alt="">
                </div>
            `;
        } else if (isVideo) {
            if (type === 'post') {
                // Thread video structure
                html += `
                    <div class="post_image" bis_skin_checked="1">
                        <div class="post_image_info" bis_skin_checked="1">
                            <a class="image_url" href="/static/${folder}/${file}" bis_skin_checked="1">
                                ${displayName}
                            </a>
                        </div>
                        <img class="post_img post_video_thumbnail" draggable="false"
                            src="/static/${thumbFolder}/thumbnail_${baseName}.jpg">
                        <video controls class="post_video"
                            src="/static/${folder}/${file}" 
                            style="display: none;"></video>
                    </div>
                `;
            } else {
                // Reply video structure
                html += `
                    <div class="reply_image" bis_skin_checked="1">
                        <div class="post_image_info" bis_skin_checked="1">
                            <a class="image_url" href="/static/${folder}/${file}" bis_skin_checked="1">
                                ${displayName}
                            </a>
                        </div>
                        <img class="reply_img post_video_thumbnail" draggable="false"
                            src="/static/${thumbFolder}/thumbnail_${baseName}.jpg">
                        <video controls draggable="false" class="reply_img post_video"
                            src="/static/${folder}/${file}" 
                            style="display: none;"></video>
                    </div>
                `;
            }
        }
    });
    
    html += '</div>';
    return html;
}
