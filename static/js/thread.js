function manipularConteudo() {
    var postContents = document.querySelectorAll('pre');

    postContents.forEach(function(postContent) {
        var content = postContent.innerHTML;

        // [wikinet]link[/wikinet]
        content = content.replace(/\[wikinet\](.*?)\[\/wikinet\]/g,
            '<a class="wikinet-hyper-link" href="https://wikinet.pro/wiki/$1" target="_blank"><span>$1</span></a>');

        // [texto](https://link)
        content = content.replace(/\[([^\]]+)\]\((https?:\/\/[^\s]+(?:\S)*)\)/g,
            '<a class="hyper-link" href="$2">$1</a>');

        // >>123
        content = content.split('&gt;&gt;').map((part, index) => {
            if (index === 0) return part;
            const number = part.match(/^\d+/);
            if (number) {
                const quotedId = number[0];
                const quotedDiv = document.querySelector(`div[id="${quotedId}"]`);
                const isOperator = quotedDiv && quotedDiv.getAttribute('post-role') === 'operator';

                const quoteSpan = `<span class="quote-reply" data-id="${quotedId}">&gt;&gt;${quotedId}</span>`;
                const operatorSpan = isOperator ? `<span class="operator-quote">(OP)</span>` : '';
                return `${quoteSpan}${operatorSpan}${part.slice(quotedId.length)}`;
            }
            return `&gt;&gt;${part}`;
        }).join('');

        postContent.innerHTML = content;
    });

    adicionarEventosQuoteReply();
}


function adicionarEventosQuoteReply() {
    const quoteReplies = document.querySelectorAll('span.quote-reply');

    quoteReplies.forEach(span => {
        span.addEventListener('click', () => {
            const targetId = span.getAttribute('data-id');
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                document.querySelectorAll('.target').forEach(el => {
                    el.style.backgroundColor = '';
                });

                targetElement.style.backgroundColor = '#6d99ba73';
                targetElement.style.borderColor = '#82cece';

                setTimeout(() => {
                    targetElement.style.backgroundColor = '';
                    targetElement.style.borderColor = '';
                }, 2000);

                targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });

                const offset = 100;
                const elementPosition = targetElement.getBoundingClientRect().top + window.scrollY;
                const offsetPosition = elementPosition - offset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });

        span.addEventListener('mouseenter', (event) => {
            const targetId = span.getAttribute('data-id');
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                const preview = targetElement.cloneNode(true);
                const replies = preview.querySelectorAll('div.replies');
                replies.forEach(reply => reply.remove());
                preview.classList.add('preview-reply');
                preview.style.position = 'absolute';
                preview.style.zIndex = '1000';
                preview.style.minWidth = '40em';
                preview.style.display = 'block';

                document.body.appendChild(preview);

                const updatePreviewPosition = (e) => {
                    preview.style.left = `${e.pageX + 10}px`;
                    preview.style.top = `${e.pageY + 10}px`;
                };

                document.addEventListener('mousemove', updatePreviewPosition);

                span.addEventListener('mouseleave', () => {
                    if (preview && document.body.contains(preview)) {
                        document.body.removeChild(preview);
                        document.removeEventListener('mousemove', updatePreviewPosition);
                    }
                });
            }
            else {
                let preview;
                let updatePreviewPosition;
                let cancelled = false;
                const onLeave = () => {
                    cancelled = true;
                    if (preview && document.body.contains(preview)) {
                        document.body.removeChild(preview);
                    }
                    if (updatePreviewPosition) {
                        document.removeEventListener('mousemove', updatePreviewPosition);
                    }
                };
                span.addEventListener('mouseleave', onLeave, { once: true });
                const buildPreview = (data) => {
                    const isReply = !!data.reply_id;
                    const container = document.createElement('div');
                    container.className = isReply ? 'reply' : 'post';
                    container.classList.add('preview-reply');
                    container.style.position = 'absolute';
                    container.style.zIndex = '1000';
                    container.style.minWidth = '40em';
                    container.style.display = 'block';
                    const info = document.createElement('div');
                    info.className = isReply ? 'reply-postInfo' : 'postInfo';
                    const nameBlock = document.createElement('span');
                    nameBlock.className = 'nameBlock';
                    const nameSpan = document.createElement('span');
                    nameSpan.className = 'name';
                    nameSpan.innerHTML = `${data.post_user || 'ドワーフ'} `;
                    nameBlock.appendChild(nameSpan);
                    const dateSpan = document.createElement('span');
                    dateSpan.className = 'postDate';
                    dateSpan.textContent = data.post_date || '';
                    const numberLinkLabel = document.createElement('a');
                    numberLinkLabel.className = 'postLink';
                    numberLinkLabel.textContent = 'No. ';
                    const numberLink = document.createElement('a');
                    numberLink.className = 'postLink';
                    numberLink.href = isReply ? `/${data.board}/thread/${data.post_id}#${isReply ? data.reply_id : data.post_id}` : `/${data.board}/thread/${data.post_id}`;
                    numberLink.textContent = isReply ? data.reply_id : data.post_id;
                    info.appendChild(nameBlock);
                    info.appendChild(dateSpan);
                    info.appendChild(numberLinkLabel);
                    info.appendChild(numberLink);
                    container.appendChild(info);
                    const contentContainer = document.createElement('div');
                    contentContainer.className = isReply ? 'post_content_container' : 'post_content_container';
                    const filesContainer = document.createElement('div');
                    filesContainer.className = isReply ? 'reply_files' : 'post_files';
                    const images = isReply ? (data.images || (data.image ? [data.image] : [])) : (data.post_images || []);
                    images.forEach((img) => {
                        if (!img) return;
                        const wrap = document.createElement('div');
                        wrap.className = isReply ? 'reply_image' : 'post_image';
                        const imgEl = document.createElement('img');
                        imgEl.draggable = false;
                        imgEl.className = isReply ? 'reply_img' : 'post_img';
                        const base = isReply ? '/static/reply_images/' : '/static/post_images/';
                        imgEl.src = base + img;
                        wrap.appendChild(imgEl);
                        filesContainer.appendChild(wrap);
                    });
                    if (images.length > 0) {
                        contentContainer.appendChild(filesContainer);
                    }
                    const textContainer = document.createElement('div');
                    textContainer.className = isReply ? 'reply_content' : 'post_content';
                    const pre = document.createElement('pre');
                    pre.innerHTML = isReply ? (data.content || '') : (data.post_content || data.original_content || '');
                    textContainer.appendChild(pre);
                    contentContainer.appendChild(textContainer);
                    container.appendChild(contentContainer);
                    return container;
                };
                if (!targetId || isNaN(Number(targetId))) {
                    return;
                }
                fetch(`/api/get_post_info?post_id=${encodeURIComponent(targetId)}`)
                    .then(r => r.ok ? r.json() : Promise.reject())
                    .then(data => {
                        if (cancelled) return;
                        preview = buildPreview(data);
                        document.body.appendChild(preview);
                        updatePreviewPosition = (e) => {
                            preview.style.left = `${e.pageX + 10}px`;
                            preview.style.top = `${e.pageY + 10}px`;
                        };
                        document.addEventListener('mousemove', updatePreviewPosition);
                    })
                    .catch(() => {})
                    .finally(() => {});
            }
        });
    });

    const crossBoardLinks = document.querySelectorAll('a.quote-reply');
    crossBoardLinks.forEach(link => {
        link.addEventListener('mouseenter', (event) => {
            const targetId = link.getAttribute('data-id');
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                const preview = targetElement.cloneNode(true);
                const replies = preview.querySelectorAll('div.replies');
                replies.forEach(reply => reply.remove());
                preview.classList.add('preview-reply');
                preview.style.position = 'absolute';
                preview.style.zIndex = '1000';
                preview.style.minWidth = '40em';
                preview.style.display = 'block';

                document.body.appendChild(preview);

                const updatePreviewPosition = (e) => {
                    preview.style.left = `${e.pageX + 10}px`;
                    preview.style.top = `${e.pageY + 10}px`;
                };

                document.addEventListener('mousemove', updatePreviewPosition);

                link.addEventListener('mouseleave', () => {
                    if (preview && document.body.contains(preview)) {
                        document.body.removeChild(preview);
                        document.removeEventListener('mousemove', updatePreviewPosition);
                    }
                }, { once: true });
            } else {
                let preview;
                let updatePreviewPosition;
                let cancelled = false;
                const onLeave = () => {
                    cancelled = true;
                    if (preview && document.body.contains(preview)) {
                        document.body.removeChild(preview);
                    }
                    if (updatePreviewPosition) {
                        document.removeEventListener('mousemove', updatePreviewPosition);
                    }
                };
                link.addEventListener('mouseleave', onLeave, { once: true });
                const buildPreview = (data) => {
                    const isReply = !!data.reply_id;
                    const container = document.createElement('div');
                    container.className = isReply ? 'reply' : 'post';
                    container.classList.add('preview-reply');
                    container.style.position = 'absolute';
                    container.style.zIndex = '1000';
                    container.style.minWidth = '40em';
                    container.style.display = 'block';
                    const info = document.createElement('div');
                    info.className = isReply ? 'reply-postInfo' : 'postInfo';
                    const nameBlock = document.createElement('span');
                    nameBlock.className = 'nameBlock';
                    const nameSpan = document.createElement('span');
                    nameSpan.className = 'name';
                    nameSpan.innerHTML = `${data.post_user || 'ドワーフ'} `;
                    nameBlock.appendChild(nameSpan);
                    const dateSpan = document.createElement('span');
                    dateSpan.className = 'postDate';
                    dateSpan.textContent = data.post_date || '';
                    const numberLinkLabel = document.createElement('a');
                    numberLinkLabel.className = 'postLink';
                    numberLinkLabel.textContent = 'No. ';
                    const numberLink = document.createElement('a');
                    numberLink.className = 'postLink';
                    numberLink.href = isReply ? `/${data.board}/thread/${data.post_id}#${isReply ? data.reply_id : data.post_id}` : `/${data.board}/thread/${data.post_id}`;
                    numberLink.textContent = isReply ? data.reply_id : data.post_id;
                    info.appendChild(nameBlock);
                    info.appendChild(dateSpan);
                    info.appendChild(numberLinkLabel);
                    info.appendChild(numberLink);
                    container.appendChild(info);
                    const contentContainer = document.createElement('div');
                    contentContainer.className = isReply ? 'post_content_container' : 'post_content_container';
                    const filesContainer = document.createElement('div');
                    filesContainer.className = isReply ? 'reply_files' : 'post_files';
                    const images = isReply ? (data.images || (data.image ? [data.image] : [])) : (data.post_images || []);
                    images.forEach((img) => {
                        if (!img) return;
                        const wrap = document.createElement('div');
                        wrap.className = isReply ? 'reply_image' : 'post_image';
                        const imgEl = document.createElement('img');
                        imgEl.draggable = false;
                        imgEl.className = isReply ? 'reply_img' : 'post_img';
                        const base = isReply ? '/static/reply_images/' : '/static/post_images/';
                        imgEl.src = base + img;
                        wrap.appendChild(imgEl);
                        filesContainer.appendChild(wrap);
                    });
                    if (images.length > 0) {
                        contentContainer.appendChild(filesContainer);
                    }
                    const textContainer = document.createElement('div');
                    textContainer.className = isReply ? 'reply_content' : 'post_content';
                    const pre = document.createElement('pre');
                    pre.innerHTML = isReply ? (data.content || '') : (data.post_content || data.original_content || '');
                    textContainer.appendChild(pre);
                    contentContainer.appendChild(textContainer);
                    container.appendChild(contentContainer);
                    return container;
                };
                if (!targetId || isNaN(Number(targetId))) {
                    return;
                }
                fetch(`/api/get_post_info?post_id=${encodeURIComponent(targetId)}`)
                    .then(r => r.ok ? r.json() : Promise.reject())
                    .then(data => {
                        if (cancelled) return;
                        preview = buildPreview(data);
                        document.body.appendChild(preview);
                        updatePreviewPosition = (e) => {
                            preview.style.left = `${e.pageX + 10}px`;
                            preview.style.top = `${e.pageY + 10}px`;
                        };
                        document.addEventListener('mousemove', updatePreviewPosition);
                    })
                    .catch(() => {})
                    .finally(() => {});
            }
        });
    });
}


function quotePostId(postId) {
    const textarea = document.getElementById('text');
    const draggableForm = document.getElementById('draggableForm');

    textarea.value += '' + (textarea.value ? '\n>>' : '>>') + postId;

    draggableForm.style.position = 'absolute';

    const mouseX = event.pageX;
    const mouseY = event.pageY + 10;

    const rightEdge = window.innerWidth - draggableForm.offsetWidth;
    const bottomEdge = window.innerHeight - draggableForm.offsetHeight;

    let newLeft = mouseX;
    let newTop = mouseY;

    if (newLeft < 0) newLeft = 0;
    if (newTop < 0) newTop = 0;
    if (newLeft > rightEdge) newLeft = rightEdge;
    if (newTop > bottomEdge) newTop = bottomEdge;

    draggableForm.style.display = 'block';
    draggableForm.style.left = `${newLeft}px`;
    draggableForm.style.top = `${newTop}px`;
}


document.addEventListener("DOMContentLoaded", function() {
    manipularConteudo();

    const textarea = document.getElementById('text');
    let quoteButton;

    document.addEventListener('mouseup', () => {
        const selection = window.getSelection();
        if (selection.toString()) {
            if (!quoteButton) {
                quoteButton = document.createElement('button');
                quoteButton.className = 'quote-button';
                quoteButton.innerText = 'Quote';
                document.body.appendChild(quoteButton);
            }

            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();

            quoteButton.style.left = `${rect.left + window.scrollX}px`;
            quoteButton.style.top = `${rect.top + window.scrollY - 10}px`;

            requestAnimationFrame(() => {
                quoteButton.style.display = 'block';
            });
        } else if (quoteButton) {
            quoteButton.style.display = 'none';
        }
    });

    document.addEventListener('click', (e) => {
        if (quoteButton && e.target !== quoteButton) {
            quoteButton.style.display = 'none';
        }
    });

    document.addEventListener('click', (e) => {
        if (quoteButton && e.target === quoteButton) {
            const selection = window.getSelection();
            const selectedText = selection.toString();
            textarea.value += '' + (textarea.value ? '\n>' : '>') + selectedText;
            quoteButton.style.display = 'none';
            window.getSelection().removeAllRanges();
        }
    });
});


document.addEventListener('DOMContentLoaded', function() {
    function formatDate(element) {
        const dateString = element.textContent.trim();

        try {
            const [datePart, timePart] = dateString.split(' ');
            const [day, month, year] = datePart.split('/').map(Number);
            const [hours, minutes, secondsRaw] = timePart.split(':').map(Number);
            const seconds = Number.isFinite(secondsRaw) ? secondsRaw : 0;
            const z2 = (n) => String(n).padStart(2, '0');
            const iso = `${year}-${z2(month)}-${z2(day)}T${z2(hours)}:${z2(minutes)}:${z2(seconds)}-03:00`;
            const serverMs = Date.parse(iso);
            const nowMs = Date.now();
            const diffInSeconds = Math.floor((nowMs - serverMs) / 1000);

            const tz = (Intl && Intl.DateTimeFormat && Intl.DateTimeFormat().resolvedOptions().timeZone) || '';
            let lang = 'en';
            if (tz.includes('Tokyo')) lang = 'jp';
            else if (tz.includes('Sao_Paulo') || tz.includes('Bahia') || tz.includes('Fortaleza') || tz.includes('Recife') || tz.includes('Belem') || tz.includes('Manaus') || tz.includes('Porto_Velho') || tz.includes('Lisbon') || tz.includes('Madeira')) lang = 'pt';
            else if (tz.includes('Madrid') || tz.includes('Mexico') || tz.includes('Argentina') || tz.includes('Bogota') || tz.includes('Lima') || tz.includes('Santiago')) lang = 'es';

            const units = [
                { key: 'year', secs: 31536000 },
                { key: 'month', secs: 2592000 },
                { key: 'week', secs: 604800 },
                { key: 'day', secs: 86400 },
                { key: 'hour', secs: 3600 },
                { key: 'minute', secs: 60 },
                { key: 'second', secs: 1 }
            ];

            const dict = {
                pt: { just: 'agora mesmo', pre: 'há', words: { year: 'ano', month: 'mês', week: 'semana', day: 'dia', hour: 'hora', minute: 'minuto', second: 'segundo' }, plural: (k) => k === 'month' ? 'es' : 's' },
                es: { just: 'justo ahora', pre: 'hace', words: { year: 'año', month: 'mes', week: 'semana', day: 'día', hour: 'hora', minute: 'minuto', second: 'segundo' }, plural: (k) => k === 'month' ? 'es' : 's' },
                en: { just: 'just now', words: { year: 'year', month: 'month', week: 'week', day: 'day', hour: 'hour', minute: 'minute', second: 'second' } },
                jp: { just: 'たった今', words: { year: '年', month: 'ヶ月', week: '週間', day: '日', hour: '時間', minute: '分', second: '秒' } }
            };

            let relativeTime = '';
            for (const u of units) {
                const interval = Math.floor(diffInSeconds / u.secs);
                if (interval >= 1) {
                    if (lang === 'jp') {
                        relativeTime = `${interval} ${dict.jp.words[u.key]}前`;
                    } else if (lang === 'en') {
                        const w = dict.en.words[u.key];
                        relativeTime = interval === 1 ? `1 ${w} ago` : `${interval} ${w}s ago`;
                    } else if (lang === 'es') {
                        const w = dict.es.words[u.key];
                        const suf = interval === 1 ? '' : dict.es.plural(u.key);
                        relativeTime = interval === 1 ? `hace 1 ${w}` : `hace ${interval} ${w}${suf}`;
                    } else {
                        const w = dict.pt.words[u.key];
                        const suf = interval === 1 ? '' : dict.pt.plural(u.key);
                        relativeTime = interval === 1 ? `há 1 ${w}` : `há ${interval} ${w}${suf}`;
                    }
                    break;
                }
            }

            if (!relativeTime) {
                relativeTime = dict[lang]?.just || dict.en.just;
            }

            element.dataset.originalDate = dateString;
            element.textContent = relativeTime;
            element.setAttribute('title', dateString);

            return true;
        } catch (e) {
            console.error('Erro ao formatar data no elemento:', element, 'Erro:', e);
            return false;
        }
    }

    function updateAllDates() {
        document.querySelectorAll('span.postDate').forEach(element => {
            if (element.dataset.originalDate) {
                element.textContent = element.dataset.originalDate;
            }
            formatDate(element);
        });
    }

    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) {
                    if (node.matches('span.postDate')) {
                        formatDate(node);
                    }
                    if (node.querySelectorAll) {
                        node.querySelectorAll('span.postDate').forEach(formatDate);
                    }
                }
            });
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    document.querySelectorAll('span.postDate').forEach(formatDate);

    setInterval(updateAllDates, 60000);
});


const checkboxes = document.querySelectorAll('#togglemodoptions');

checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', () => {
        const parentDiv = checkbox.closest('div');
        const threadModOptions = parentDiv.querySelector('#threadmodoptions');
        if (threadModOptions) {
            threadModOptions.style.display = checkbox.checked ? 'flex' : 'none';
        }
    });
});


function closeModal(dialogElement) {
    if (dialogElement && dialogElement.close) {
        dialogElement.close();
    }
}


document.addEventListener('click', function(event) {
    const triggerClasses = ['ban', 'delete', 'report', 'move'];
    const triggerSelector = triggerClasses.map(cls => '.' + cls).join(', ');
    const clickedTrigger = event.target.closest(triggerSelector);

    if (clickedTrigger) {
        event.preventDefault();
        let dialogClass = null;

        for (const cls of triggerClasses) {
            if (clickedTrigger.classList.contains(cls)) {
                dialogClass = 'popup-' + cls;
                break;
            }
        }

        if (dialogClass) {
            let parent = clickedTrigger.parentElement;
            let dialog = null;

            while (parent) {
                dialog = parent.querySelector('.' + dialogClass);
                if (dialog) break;
                parent = parent.parentElement;
            }

            if (dialog) {
                dialog.showModal();
            } else {
                console.error('Erro: Dialog com a classe "' + dialogClass + '" não encontrado próximo ao botão.');
            }
        }
    }
});


document.addEventListener('click', function(event) {
    document.querySelectorAll('dialog[open]').forEach(dialog => {
        if (event.target === dialog) {
            dialog.close();
        }
    });
});

document.getElementById('postform').addEventListener('submit', function() {
    var btn = document.getElementById('submitpost');
    if (btn) {
        btn.disabled = true;
        btn.value = 'Posting...';
    }
});

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts[1].split(';')[0];
    return '';
}

function setCookie(name, value, days) {
    let expires = '';
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
        expires = '; expires=' + date.toUTCString();
    }
    document.cookie = name + '=' + value + expires + '; path=/; SameSite=Lax';
}

function lerThreadsOcultas() {
    const c = getCookie('hidden_threads');
    if (!c) return new Set();
    return new Set(c.split(',').map(s => s.trim()).filter(Boolean));
}

function salvarThreadsOcultas(set) {
    const value = Array.from(set).join(',');
    setCookie('hidden_threads', value, 365);
}

function aplicarVisibilidadeThread(id, ocultar) {
    const post = document.getElementById(id);
    if (!post) return;
    const content = post.querySelector('.post_content_container');
    const link = post.querySelector('a.hide-thread');
    if (content) content.style.display = ocultar ? 'none' : '';
    if (link) link.textContent = ocultar ? '[+]' : '[-]';
}

document.addEventListener('DOMContentLoaded', function() {
    const ocultas = lerThreadsOcultas();
    document.querySelectorAll('a.hide-thread').forEach(a => {
        const id = a.getAttribute('thread_to_hide');
        if (!id) return;
        if (ocultas.has(id)) aplicarVisibilidadeThread(id, true);
        a.addEventListener('click', function(e) {
            e.preventDefault();
            const idClick = a.getAttribute('thread_to_hide');
            if (!idClick) return;
            if (ocultas.has(idClick)) {
                ocultas.delete(idClick);
                aplicarVisibilidadeThread(idClick, false);
            } else {
                ocultas.add(idClick);
                aplicarVisibilidadeThread(idClick, true);
            }
            salvarThreadsOcultas(ocultas);
        });
    });
});
