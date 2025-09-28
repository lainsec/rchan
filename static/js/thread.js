function manipularConteudo() {
    var postContents = document.querySelectorAll('pre');

    postContents.forEach(function(postContent) {
        var content = postContent.innerHTML;

        content = content.replace(/\[wikinet\](.*?)\[\/wikinet\]/g, '<a class="wikinet-hyper-link" href="https://wikinet.pro/wiki/$1" target="_blank"><span>$1</span></a>');

        content = content.replace(/\[([^\]]+)\]\((https?:\/\/[^\s]+(?:\S)*)\)/g, '<a class="hyper-link" href="$2">$1</a>');

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

        content = content.split('&gt;').map((part, index) => {
            if (index === 0) return part;
            const match = part.match(/^[^<&\n]+/);
            return match ? `<span class="verde">&gt;${match}</span>${part.slice(match[0].length)}` : `&gt;${part}`;
        }).join('');

        content = content.split('&lt;').map((part, index) => {
            if (index === 0) return part;
            const match = part.match(/^[^<&\n]+/);
            return match ? `<span class="vermelho">&lt;${match}</span>${part.slice(match[0].length)}` : `&lt;${part}`;
        }).join('');

        content = content.split('(((').map((part, index) => {
            if (index === 0) return part;
            const match = part.match(/^([^\)]+)\)\)\)(.*)/);
            return match ? `<span class="detected">(((${match[1]})))</span>${match[2]}` : `(((${part}`;
        }).join('');

        content = content.split('==').map((part, index) => {
            if (index % 2 === 1) return `<span class="red-text">${part}</span>`;
            return part;
        }).join('');

        content = content.split('||').map((part, index) => {
            if (index % 2 === 1) return `<span class="spoiler">${part}</span>`;
            return part;
        }).join('');

        content = content.split('[spoiler]').join('<span class="spoiler">').split('[/spoiler]').join('</span>');

        content = content.split('[r]').join('<span class="rainbowtext">').split('[/r]').join('</span>');

        postContent.innerHTML = content;
    });
    adicionarEventosQuoteReply();
}


function adicionarEventosQuoteReply() {

    const quoteReplies = document.querySelectorAll('.quote-reply');

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
                if (!preview.style.backgroundColor) {
                    preview.style.backgroundColor = 'var(--cor-fundo-claro)';
                }
                preview.style.position = 'absolute';
                preview.style.zIndex = '1000';
                preview.style.border = '1px solid var(--cor-borda)';
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
                quoteButton.innerText = 'Quotar';
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
    // Função principal que formata a data
    function formatDate(element) {
        const dateString = element.textContent.trim();
        
        try {
            // Converte a string para um objeto Date (formato dd/mm/aaaa HH:MM:SS)
            const [datePart, timePart] = dateString.split(' ');
            const [day, month, year] = datePart.split('/').map(Number);
            const [hours, minutes, seconds] = timePart.split(':').map(Number);
            
            const date = new Date(year, month - 1, day, hours, minutes, seconds);
            
            // Calcula a diferença em relação ao agora
            const now = new Date();
            const diffInSeconds = Math.floor((now - date) / 1000);
            
            // Define os intervalos de tempo
            const intervals = {
                ano: 31536000,
                mês: 2592000,
                semana: 604800,
                dia: 86400,
                hora: 3600,
                minuto: 60,
                segundo: 1
            };
            
            // Calcula o tempo relativo
            let relativeTime = '';
            for (const [unit, secondsInUnit] of Object.entries(intervals)) {
                const interval = Math.floor(diffInSeconds / secondsInUnit);
                if (interval >= 1) {
                    relativeTime = interval === 1 ? 
                        `há 1 ${unit}` : 
                        `há ${interval} ${unit}${unit !== 'mês' ? 's' : 'es'}`;
                    break;
                }
            }
        
            if (!relativeTime) {
                relativeTime = 'agora mesmo';
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

    // Função para atualizar todas as datas periodicamente
    function updateAllDates() {
        document.querySelectorAll('span.postDate').forEach(element => {
            // Restaura a data original antes de formatar novamente
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

document.addEventListener('click', function (event) {
    const triggerClasses = ['ban', 'delete', 'move'];

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

document.addEventListener('click', function (event) {
    document.querySelectorAll('dialog[open]').forEach(dialog => {
        if (event.target === dialog) {
            dialog.close();
        }
    });
});