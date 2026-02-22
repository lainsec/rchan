document.getElementById('togglePostFormLink').addEventListener('click', function(event) {
    event.preventDefault();
    
    var formDiv = document.querySelector('.newboard-form');
    var currentDisplay = window.getComputedStyle(formDiv).display;
    
    if (currentDisplay === 'none' || !formDiv.style.display) {
        formDiv.style.display = 'block';
        formDiv.style.position = 'fixed';

        const formWidth = formDiv.offsetWidth;
        const formHeight = formDiv.offsetHeight;

        let clickX = typeof event.clientX === 'number' ? event.clientX : window.innerWidth / 2;
        let clickY = typeof event.clientY === 'number' ? event.clientY : window.innerHeight / 2;

        let newLeft = clickX;
        let newTop = clickY + 10;

        if (formWidth >= window.innerWidth) {
            newLeft = 0;
        } else {
            if (newLeft + formWidth > window.innerWidth) newLeft = window.innerWidth - formWidth;
            if (newLeft < 0) newLeft = 0;
        }

        if (formHeight >= window.innerHeight) {
            newTop = 0;
        } else {
            if (newTop + formHeight > window.innerHeight) newTop = window.innerHeight - formHeight;
            if (newTop < 0) newTop = 0;
        }

        formDiv.style.left = newLeft + 'px';
        formDiv.style.top = newTop + 'px';
    } else {
        formDiv.style.display = 'none'; 
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const closeButtons = document.querySelectorAll('.close.postform-style');
    const formContainer = document.getElementById('draggableForm');
    const messageLabel = document.querySelector('.row .label span + small');
    const messageTextarea = document.getElementById('text');

    closeButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();

            if (formContainer.style.display === 'none') {
                formContainer.style.display = 'block';
            } else {
                formContainer.style.display = 'none';
            }
        });
    });

    if (messageLabel && messageTextarea) {
        const originalText = messageLabel.textContent.trim();
        const match = originalText.match(/^\((\d+)\s*\/\s*(\d+)\)$/);
        let max = 20000;
        if (match) {
            max = parseInt(match[2], 10) || max;
        }
        function updateCounter() {
            const len = messageTextarea.value.length;
            messageLabel.textContent = `(${len}/${max})`;
            if (len > max) {
                messageLabel.style.color = '#d9534f';
            } else {
                messageLabel.style.color = '';
            }
        }
        updateCounter();
        messageTextarea.addEventListener('input', updateCounter);
    }
});

const draggableForm = document.getElementById('draggableForm');
const header = document.querySelector('.new-thread-header'); 
draggableForm.style.position = 'fixed';

function initDrag(startClientX, startClientY, getCoords) {
    const style = window.getComputedStyle(draggableForm);
    let startLeft = parseInt(style.left || '0', 10);
    let startTop = parseInt(style.top || '0', 10);

    if (isNaN(startLeft) || isNaN(startTop)) {
        const rect = draggableForm.getBoundingClientRect();
        startLeft = rect.left + window.scrollX;
        startTop = rect.top + window.scrollY;
    }

    function moveAt(clientX, clientY) {
        const dx = clientX - startClientX;
        const dy = clientY - startClientY;

        let newLeft = startLeft + dx;
        let newTop = startTop + dy;

        const maxLeft = window.innerWidth - draggableForm.offsetWidth;
        const maxTop = window.innerHeight - draggableForm.offsetHeight;

        if (newLeft < 0) newLeft = 0;
        if (newLeft > maxLeft) newLeft = maxLeft < 0 ? 0 : maxLeft;

        if (newTop < 0) newTop = 0;
        if (newTop > maxTop) newTop = maxTop < 0 ? 0 : maxTop;

        draggableForm.style.left = newLeft + 'px';
        draggableForm.style.top = newTop + 'px';
    }

    function onMove(e) {
        const coords = getCoords(e);
        if (!coords) return;
        moveAt(coords.clientX, coords.clientY);
        if (e.cancelable) {
            e.preventDefault();
        }
    }

    function stop() {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', stop);
        document.removeEventListener('touchmove', onMove);
        document.removeEventListener('touchend', stop);
    }

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', stop);
    document.addEventListener('touchmove', onMove, { passive: false });
    document.addEventListener('touchend', stop);

    draggableForm.ondragstart = function() {
        return false; 
    };
}

header.addEventListener('mousedown', function(e) {
    initDrag(e.clientX, e.clientY, function(ev) {
        return { clientX: ev.clientX, clientY: ev.clientY };
    });
    e.preventDefault();
});

header.addEventListener('touchstart', function(e) {
    if (!e.touches || e.touches.length === 0) return;
    const touch = e.touches[0];
    initDrag(touch.clientX, touch.clientY, function(ev) {
        const t = ev.touches && ev.touches[0] ? ev.touches[0] : ev.changedTouches && ev.changedTouches[0] ? ev.changedTouches[0] : null;
        if (!t) return null;
        return { clientX: t.clientX, clientY: t.clientY };
    });
    if (e.cancelable) {
        e.preventDefault();
    }
}, { passive: false });

document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('post-file-uploader');
    const uploadList = document.querySelector('.upload-list');
    const fileLabel = document.querySelector('.filelabel');
    const MAX_FILES = 4;

    let selectedFiles = [];
    let fileOptions = [];

    function generateUUID() {
        if (window.crypto && window.crypto.randomUUID) {
            return window.crypto.randomUUID();
        }
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    function handleFiles(files) {
        const newFiles = Array.from(files).filter(file =>
            file.type.startsWith('image/') || file.type.startsWith('video/')
        );
        if (newFiles.length === 0) return;

        const totalAfterAdd = selectedFiles.length + newFiles.length;
        if (totalAfterAdd > MAX_FILES) {
            alert(`You can upload a maximum of ${MAX_FILES} files.`);
            return;
        }

        newFiles.forEach(newFile => {
            const alreadyExists = selectedFiles.some(file =>
                file.name === newFile.name &&
                file.size === newFile.size &&
                file.lastModified === newFile.lastModified
            );
            if (!alreadyExists) {
                selectedFiles.push(newFile);
                fileOptions.push({
                    spoiler: false,
                    strip: false,
                    uuid: generateUUID()
                });
            }
        });

        updateFileInput();
        renderPreviews();
    }

    function updateFileInput() {
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach(file => dataTransfer.items.add(file));
        fileInput.files = dataTransfer.files;
    }

    function renderPreviews() {
        uploadList.innerHTML = '';
        selectedFiles.forEach((file, index) => {
            createFilePreview(file, index, fileOptions[index]);
        });

        fileLabel.style.display = selectedFiles.length > 0 ? 'none' : 'flex';
    }

    function createFilePreview(file, index, options) {
        const previewItem = document.createElement('div');
        previewItem.className = 'file-preview';

        const row = document.createElement('div');
        row.className = 'file-preview-row';

        let media;
        if (file.type.startsWith('image/')) {
            media = document.createElement('img');
            media.src = URL.createObjectURL(file);
        } else if (file.type.startsWith('video/')) {
            media = document.createElement('video');
            media.src = URL.createObjectURL(file);
            media.controls = true;
            media.muted = true;
        }

        const originalName = file.name;

        const fileName = document.createElement('span');
        fileName.className = 'file-preview-name';

        function applyName() {
            let displayName = originalName;
            const dot = originalName.lastIndexOf('.');
            const ext = dot !== -1 ? originalName.slice(dot) : '';

            if (options.strip && options.spoiler) {
                displayName = 'spoiler-' + options.uuid + ext;
            } else if (options.strip) {
                displayName = options.uuid + ext;
            } else if (options.spoiler) {
                displayName = 'spoiler-' + originalName;
            }

            fileName.textContent = displayName.length > 15
                ? displayName.substring(0, 12) + '...' : displayName;
        }

        const removeBtn = document.createElement('button');
        removeBtn.innerHTML = '×';
        removeBtn.className = 'file-preview-remove';

        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            removeFile(index);
        });

        const leftWrapper = document.createElement('div');
        leftWrapper.className = 'file-preview-left';
        leftWrapper.appendChild(media);

        const rightWrapper = document.createElement('div');
        rightWrapper.className = 'file-preview-right';
        rightWrapper.appendChild(fileName);
        rightWrapper.appendChild(removeBtn);

        row.appendChild(leftWrapper);
        row.appendChild(rightWrapper);
        previewItem.appendChild(row);

        const optionsRow = document.createElement('div');
        optionsRow.className = 'file-preview-options';

        const spoilerLabel = document.createElement('label');
        const spoilerCheckbox = document.createElement('input');
        spoilerCheckbox.type = 'checkbox';
        spoilerCheckbox.checked = options.spoiler;
        spoilerLabel.appendChild(spoilerCheckbox);
        spoilerLabel.appendChild(document.createTextNode('spoiler'));

        const stripLabel = document.createElement('label');
        const stripCheckbox = document.createElement('input');
        stripCheckbox.type = 'checkbox';
        stripCheckbox.checked = options.strip;
        stripLabel.appendChild(stripCheckbox);
        stripLabel.appendChild(document.createTextNode('strip filename'));

        spoilerCheckbox.addEventListener('change', () => {
            options.spoiler = spoilerCheckbox.checked;
            applyName();
        });

        stripCheckbox.addEventListener('change', () => {
            options.strip = stripCheckbox.checked;
            applyName();
        });

        optionsRow.appendChild(spoilerLabel);
        optionsRow.appendChild(stripLabel);
        previewItem.appendChild(optionsRow);

        applyName();
        uploadList.appendChild(previewItem);
    }

    function removeFile(index) {
        selectedFiles.splice(index, 1);
        fileOptions.splice(index, 1);
        updateFileInput();
        renderPreviews();
    }

    function setupDragDrop(element) {
        element.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            element.style.border = '2px dashed var(--cor-secundaria)';
        });

        element.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            element.style.border = '';
        });

        element.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            element.style.border = '';
            if (e.dataTransfer.files.length > 0) {
                handleFiles(e.dataTransfer.files);
            }
        });
    }

    document.addEventListener('paste', (e) => {
        const items = (e.clipboardData || window.clipboardData).items;
        const files = [];

        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            if (item.kind === 'file' &&
                (item.type.startsWith('image/') || item.type.startsWith('video/'))) {
                const file = item.getAsFile();
                if (file) files.push(file);
            }
        }

        if (files.length > 0) {
            handleFiles(files);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFiles(e.target.files);
        }
    });

    setupDragDrop(fileInput);
    setupDragDrop(fileLabel);

    const form = document.getElementById('postform');
    if (form) {
        form.addEventListener('submit', () => {
            let hidden = form.querySelector('input[name="fileOptions"]');
            if (!hidden) {
                hidden = document.createElement('input');
                hidden.type = 'hidden';
                hidden.name = 'fileOptions';
                form.appendChild(hidden);
            }
            hidden.value = JSON.stringify(fileOptions);
        });
    }
});
