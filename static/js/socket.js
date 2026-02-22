var jQuery = jQuery.noConflict();
var socket = io();

const notification_path = '/static/audios/notification.mp3';
const notification = new Audio(notification_path);
let notificationReady = false;
try {
    notification.addEventListener('canplaythrough', function () {
        notificationReady = true;
    });
} catch (e) {}
function playNotification() {
    try {
        if (notificationReady) {
            notification.currentTime = 0;
            notification.play().catch(function () {});
        }
    } catch (e) {}
}
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

function shouldHaveRainbowText(id) {
    const s = String(id);
    if (s === '1') return true;
    if (s.length >= 2) {
        const last = s[s.length - 1];
        const secondLast = s[s.length - 2];
        return last === secondLast;
    }
    return false;
}

let catalogOriginalOrder = [];
let catalogCurrentSort = 'bump';

function parseCatalogDate(element) {
    const dateSpan = element.querySelector('.catalog-post-info .postDate');
    if (!dateSpan) {
        const idFallback = parseInt(element.id, 10);
        return isNaN(idFallback) ? 0 : idFallback;
    }
    const raw = (dateSpan.getAttribute('data-original-date') || dateSpan.getAttribute('title') || dateSpan.textContent || '').trim();
    if (!raw) {
        const idFallback = parseInt(element.id, 10);
        return isNaN(idFallback) ? 0 : idFallback;
    }
    const m = raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?$/);
    if (m) {
        const day = parseInt(m[1], 10);
        const month = parseInt(m[2], 10) - 1;
        const year = parseInt(m[3], 10);
        const hour = parseInt(m[4], 10);
        const minute = parseInt(m[5], 10);
        const second = m[6] ? parseInt(m[6], 10) : 0;
        const dt = new Date(year, month, day, hour, minute, second);
        const t = dt.getTime();
        if (!isNaN(t)) return t;
    }
    const t2 = Date.parse(raw);
    if (!isNaN(t2)) return t2;
    const idFallback = parseInt(element.id, 10);
    return isNaN(idFallback) ? 0 : idFallback;
}

function applyCatalogBumpSort() {
    const container = document.querySelector('.catalog-container');
    if (!container || catalogOriginalOrder.length === 0) return;
    catalogCurrentSort = 'bump';
    catalogOriginalOrder.forEach(function (el) {
        if (el.parentNode === container) {
            container.appendChild(el);
        }
    });
}

function applyCatalogDateSort() {
    const container = document.querySelector('.catalog-container');
    if (!container) return;
    catalogCurrentSort = 'date';
    var posts = Array.prototype.slice.call(container.querySelectorAll('.catalog-post'));
    posts.sort(function (a, b) {
        return parseCatalogDate(b) - parseCatalogDate(a);
    });
    posts.forEach(function (el) {
        container.appendChild(el);
    });
}

function initCatalogSorting() {
    const container = document.querySelector('.catalog-container');
    if (!container) return;
    catalogOriginalOrder = Array.prototype.slice.call(container.querySelectorAll('.catalog-post'));
    const select = document.getElementById('catalogSortSelect');
    if (select) {
        select.value = catalogCurrentSort;
        const reapply = function () {
            if (select.value === 'date') {
                applyCatalogDateSort();
            } else {
                applyCatalogBumpSort();
            }
        };
        select.addEventListener('change', reapply);
        select.addEventListener('input', reapply);
        select.addEventListener('click', reapply);
        select.addEventListener('mousedown', function () { setTimeout(reapply, 0); });
        select.addEventListener('keyup', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                reapply();
            }
        });
        reapply();
    }
}

function initCatalogSearch() {
    const input = document.getElementById('catalogSearchInput');
    const container = document.querySelector('.catalog-container');
    if (!input || !container) return;
    const posts = Array.prototype.slice.call(container.querySelectorAll('.catalog-post'));
    input.addEventListener('input', function () {
        const query = input.value.toLowerCase();
        posts.forEach(function (el) {
            if (!query) {
                el.style.display = '';
                return;
            }
            const info = el.querySelector('.catalog-post-info');
            const content = el.querySelector('.catalog-post-content pre');
            const nameEl = info ? info.querySelector('.name') : null;
            const idLink = info ? info.querySelector('.postNumber') : null;
            const parts = [];
            if (nameEl && nameEl.textContent) parts.push(nameEl.textContent.toLowerCase());
            if (idLink && idLink.textContent) parts.push(idLink.textContent.toLowerCase());
            if (content && content.textContent) parts.push(content.textContent.toLowerCase());
            const haystack = parts.join(' ');
            if (haystack.indexOf(query) !== -1) {
                el.style.display = '';
            } else {
                el.style.display = 'none';
            }
        });
    });
}

function generateCatalogThumbHTML(files, mediaApproved) {
    if (!files || files.length === 0) {
        return '';
    }
    if (mediaApproved === 0) {
        return '<img src="/static/imgs/decoration/mediapendingapproval.png">';
    }
    const file = files[0];
    if (file.indexOf('youtube:') === 0) {
        const parts = file.split(':');
        const videoId = parts.length > 1 ? parts[1] : '';
        if (!videoId) {
            return '';
        }
        return '<img src="https://img.youtube.com/vi/' + videoId + '/0.jpg">';
    }
    const segments = file.split('.');
    const extension = segments.length > 1 ? segments[segments.length - 1].toLowerCase() : '';
    if (extension === 'mp4' || extension === 'mov' || extension === 'webm') {
        const baseName = file.substring(0, file.length - extension.length - 1);
        return '<img src="/static/post_images/thumbs/thumbnail_' + baseName + '.jpg">';
    }
    return '<img src="/static/post_images/' + file + '">';
}

function addNewCatalogThread(post) {
    const container = document.querySelector('.catalog-container');
    if (!container) return;
    const displayName = post.name === '' ? 'ドワーフ' : post.name;
    const filesCount = post.files ? post.files.length : 0;
    const thumbHTML = generateCatalogThumbHTML(post.files, post.media_approved);
    const rainbowClass = shouldHaveRainbowText(post.id) ? ' rainbowtext' : '';
    const threadHTML = ''
        + '<div class="catalog-post" id="' + post.id + '">'
        + '    <div class="catalog-post-info">'
        + '        <input type="checkbox" name="" id="">'
        + '        <span class="name">' + displayName + '</span>'
        + '        <span class="postDate" data-original-date="' + post.date + '" title="' + post.date + '">agora mesmo</span>'
        + '        <a href="/' + post.board + '/thread/' + post.id + '" class="postLink">No. </a> '
        + '        <a class="postLink' + rainbowClass + '" href="/' + post.board + '/thread/' + post.id + '" class="postNumber">' + post.id + '</a>'
        + '        <a class="postLink" href="/' + post.board + '/thread/' + post.id + '"> [Replies]</a>'
        + '        <div class="catalog-post-counter">'
        + '            R: 0 / F: ' + filesCount + ' / P: 1'
        + '        </div>'
        + '    </div>'
        + '    <div class="catalog-post-file">'
        + '        <a href="/' + post.board + '/thread/' + post.id + '">'
        +              thumbHTML
        + '        </a>'
        + '    </div>'
        + '    <div class="catalog-post-content">'
        + '        <pre>' + post.content + '</pre>'
        + '    </div>'
        + '</div>';
    container.insertAdjacentHTML('afterbegin', threadHTML);
    const newElement = container.querySelector('.catalog-post');
    if (newElement) {
        catalogOriginalOrder.unshift(newElement);
        if (catalogCurrentSort === 'date') {
            applyCatalogDateSort();
        }
    }
}

function moveCatalogThreadToTop(threadId) {
    const el = document.getElementById(String(threadId));
    if (!el) return;
    const container = el.closest('.catalog-container') || document.querySelector('.catalog-container');
    if (!container || !container.contains(el)) return;
    const firstEl = container.firstElementChild;
    if (firstEl) {
        container.insertBefore(el, firstEl);
    } else {
        container.appendChild(el);
    }
    const idx = catalogOriginalOrder.indexOf(el);
    if (idx > -1) catalogOriginalOrder.splice(idx, 1);
    catalogOriginalOrder.unshift(el);
}

function updateCatalogPostDate(threadId, dateStr) {
    const el = document.getElementById(String(threadId));
    if (!el) return;
    const dateSpan = el.querySelector('.catalog-post-info .postDate');
    if (!dateSpan) return;
    dateSpan.textContent = 'agora mesmo';
    if (dateStr) {
        dateSpan.setAttribute('data-original-date', dateStr);
        dateSpan.setAttribute('title', dateStr);
    }
}

function incrementCatalogReplyCount(threadId) {
    const el = document.getElementById(String(threadId));
    if (!el) return;
    const counter = el.querySelector('.catalog-post-counter');
    if (!counter) return;
    const text = counter.textContent.trim();
    const m = text.match(/R:\s*(\d+)\s*\/\s*F:\s*(\d+)\s*\/\s*P:\s*(\d+)/);
    if (m) {
        const r = parseInt(m[1], 10) || 0;
        const f = m[2];
        const p = m[3];
        const newR = r + 1;
        counter.textContent = 'R: ' + newR + ' / F: ' + f + ' / P: ' + p;
    } else {
        const nums = text.match(/\d+/g) || [];
        const r = nums.length > 0 ? parseInt(nums[0], 10) || 0 : 0;
        const f = nums.length > 1 ? nums[1] : '0';
        const p = nums.length > 2 ? nums[2] : '1';
        const newR = r + 1;
        counter.textContent = 'R: ' + newR + ' / F: ' + f + ' / P: ' + p;
    }
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
        playNotification();
    }
    
    if (isSameBoard) {
        if (data.type === 'New Thread') {
            if (currentPath === `/${currentBoard}` || currentPath === `/${currentBoard}/`) {
                addNewThread(data.post);
                markUnseenById(data.post.id);
            } else if (currentPath === `/${currentBoard}/catalog` || currentPath === `/${currentBoard}/catalog/`) {
                addNewCatalogThread(data.post);
                markUnseenById(data.post.id);
            }
        } else if (data.type === 'New Reply') {
            const parentThread = document.getElementById(data.post.thread_id);
            if (parentThread) {
                addNewReply(data.post);
                markUnseenById(data.post.id);
            }
            if (currentPath === `/${currentBoard}/catalog` || currentPath === `/${currentBoard}/catalog/`) {
                updateCatalogPostDate(data.post.thread_id, data.post.date);
                const el = document.getElementById(String(data.post.thread_id));
                if (el) {
                    const idx = catalogOriginalOrder.indexOf(el);
                    if (idx > -1) catalogOriginalOrder.splice(idx, 1);
                    catalogOriginalOrder.unshift(el);
                    if (catalogCurrentSort === 'bump') {
                        moveCatalogThreadToTop(data.post.thread_id);
                    }
                    incrementCatalogReplyCount(data.post.thread_id);
                }
            }
        }
    }
});

function initCatalogFeatures() {
    initCatalogSorting();
    initCatalogSearch();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
        initCatalogFeatures();
    });
} else {
    initCatalogFeatures();
}

function addNewThread(post) {
    const displayName = post.name === '' ? 'ドワーフ' : post.name;
    const rainbowClass = shouldHaveRainbowText(post.id) ? ' rainbowtext' : '';
    
    const threadHTML = `
        <div class="divisoria"></div>
        <div class="post" post-role="${post.role}" id="${post.id}" bis_skin_checked="1">
            <div class="postInfo" bis_skin_checked="1">
                <a href="javascript:void(0);" title="hide thread" class="hide-thread" thread_to_hide="${post.id}" style="color: #000; text-decoration: none; letter-spacing: 1.5px;">[-]</a>
                <input id="togglemodoptions" type="checkbox" class="deletionCheckBox" name="${post.id}" form="banDeleteForm">
                <span class="nameBlock"><span class="name">${displayName}</span></span>
                <span class="postDate" data-original-date="${post.date}" title="${post.date}">agora mesmo</span>
                <a href="/${post.board}/thread/${post.id}" class="postLink" bis_skin_checked="1">No. </a> 
                <a class="postLink${rainbowClass}" href="/${post.board}/thread/${post.id}" bis_skin_checked="1">${post.id}</a>
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
    const displayName = reply.name === '' ? 'ドワーフ' : reply.name;
    const rainbowClass = shouldHaveRainbowText(reply.id) ? ' rainbowtext' : '';
    
    const replyHTML = `
        <div class="reply" id="${reply.id}" bis_skin_checked="1">
            <div class="reply-postInfo" bis_skin_checked="1">
                <input id="togglemodoptions" type="checkbox" class="deletionCheckBox" name="${reply.id}" form="banDeleteForm">
                <span class="nameBlock"><span class="name">${displayName}</span></span>
                <span class="postDate" data-original-date="${reply.date}" title="${reply.date}">agora mesmo</span>
                <a href="/${reply.board}/thread/${reply.thread_id}" class="postLink" bis_skin_checked="1">No. </a> 
                <a class="postLink${rainbowClass}" href="/${reply.board}/thread/${reply.thread_id}#${reply.id}" onclick="quotePostId(event, ${reply.id}); return false;" bis_skin_checked="1">${reply.id}</a>
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
    
    const parentThreadEl = document.getElementById(String(reply.thread_id));
    const repliesContainer = parentThreadEl ? parentThreadEl.querySelector('.replies') : null;
    
    if (repliesContainer) {
        const hiddenReplies = repliesContainer.querySelector('.hidden-replies');
        if (hiddenReplies) {
            hiddenReplies.insertAdjacentHTML('beforebegin', replyHTML);
        } else {
            repliesContainer.insertAdjacentHTML('beforeend', replyHTML);
        }
        
        const isThreadPage = window.location.pathname.match(/\/[^\/]+\/thread\/\d+/);
        if (!isThreadPage) {
            const parentThread = document.getElementById(String(reply.thread_id));
            if (parentThread) {
                const postsBoard = document.getElementById('posts_board');
                if (postsBoard) {
                    const firstElement = postsBoard.firstElementChild;
                    const previousDivider = parentThread.previousElementSibling;

                    if (previousDivider && previousDivider.classList.contains('divisoria')) {
                        if (firstElement) {
                            postsBoard.insertBefore(previousDivider, firstElement);
                            postsBoard.insertBefore(parentThread, previousDivider.nextSibling);
                        } else {
                            postsBoard.appendChild(previousDivider);
                            postsBoard.appendChild(parentThread);
                        }
                    } else {
                        const newDivider = document.createElement('div');
                        newDivider.className = 'divisoria';
                        if (firstElement) {
                            postsBoard.insertBefore(newDivider, firstElement);
                            postsBoard.insertBefore(parentThread, newDivider.nextSibling);
                        } else {
                            postsBoard.appendChild(newDivider);
                            postsBoard.appendChild(parentThread);
                        }
                    }
                }
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
        const isSpoiler = baseName.startsWith('spoiler-');
        const spoilerClass = isSpoiler ? ' media-spoiler' : '';
        
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
                    <img draggable="false" class="${type === 'post' ? 'post_img' : 'reply_img'}${spoilerClass}" src="/static/${folder}/${file}" alt="">
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
                        <img class="post_img post_video_thumbnail${spoilerClass}" draggable="false"
                            src="/static/${thumbFolder}/thumbnail_${baseName}.jpg">
                        <video controls class="post_video${spoilerClass}"
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
                        <img class="reply_img post_video_thumbnail${spoilerClass}" draggable="false"
                            src="/static/${thumbFolder}/thumbnail_${baseName}.jpg">
                        <video controls draggable="false" class="reply_img post_video${spoilerClass}"
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

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
        initCatalogSorting();
    });
} else {
    initCatalogSorting();
}
