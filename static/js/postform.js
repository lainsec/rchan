document.getElementById('togglePostFormLink').addEventListener('click', function(event) {
    event.preventDefault();
    
    var formDiv = document.querySelector('.newboard-form');
    var currentDisplay = window.getComputedStyle(formDiv).display;
    
    if (currentDisplay === 'none' || !formDiv.style.display) {
        formDiv.style.display = 'block';
        formDiv.style.position = 'absolute'; 
        
        let newLeft = event.pageX;
        let newTop = event.pageY + 10;

        const rightEdge = window.innerWidth - formDiv.offsetWidth;
        const bottomEdge = document.body.scrollHeight - formDiv.offsetHeight;

        if (newLeft < 0) newLeft = 0;
        if (newTop < 0) newTop = 0;
        if (newLeft > rightEdge) newLeft = rightEdge;
        if (newTop > bottomEdge) newTop = bottomEdge;

        formDiv.style.left = newLeft + 'px'; 
        formDiv.style.top = newTop + 'px'; 
    } else {
        formDiv.style.display = 'none'; 
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const closeButtons = document.querySelectorAll('.close.postform-style');
    const formContainer = document.getElementById('draggableForm');

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
});

const draggableForm = document.getElementById('draggableForm');
const header = document.querySelector('.new-thread-header'); 
draggableForm.style.position = 'absolute';

header.addEventListener('mousedown', function(e) {
    let isDragging = false;
    let rect = draggableForm.getBoundingClientRect();
    let shiftX = e.clientX - rect.left;
    let shiftY = e.clientY - rect.top;

    function moveAt(pageX, pageY) {
        let newLeft = pageX - shiftX;
        let newTop = pageY - shiftY;

        const rightEdge = window.innerWidth - draggableForm.offsetWidth;
        const bottomEdge = document.body.scrollHeight - draggableForm.offsetHeight;

        if (newLeft < 0) newLeft = 0;
        if (newTop < 0) newTop = 0;
        if (newLeft > rightEdge) newLeft = rightEdge;
        if (newTop > bottomEdge) newTop = bottomEdge;

        draggableForm.style.left = newLeft + 'px';
        draggableForm.style.top = newTop + 'px';
    }

    function onMouseMove(e) {
        if (!isDragging) {
            isDragging = true;
        }
        moveAt(e.pageX, e.pageY);
    }

    document.addEventListener('mousemove', onMouseMove);

    function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
    }

    document.addEventListener('mouseup', onMouseUp);

    draggableForm.ondragstart = function() {
        return false; 
    };

    e.preventDefault();
});

document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('post-file-uploader');
    const uploadList = document.querySelector('.upload-list');
    const fileLabel = document.querySelector('.filelabel');
    const MAX_FILES = 4;

    let selectedFiles = [];

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
            createFilePreview(file, index);
        });

        fileLabel.style.display = selectedFiles.length > 0 ? 'none' : 'flex';
    }

    function createFilePreview(file, index) {
        const previewItem = document.createElement('div');
        previewItem.className = 'file-preview';
        previewItem.style.display = 'flex';
        previewItem.style.flexDirection = 'column';
        previewItem.style.alignItems = 'center';
        previewItem.style.margin = '10px';
        previewItem.style.position = 'relative';

        let media;
        if (file.type.startsWith('image/')) {
            media = document.createElement('img');
            media.src = URL.createObjectURL(file);
            media.style.objectFit = 'cover';
        } else if (file.type.startsWith('video/')) {
            media = document.createElement('video');
            media.src = URL.createObjectURL(file);
            media.controls = true;
            media.muted = true;
            media.style.objectFit = 'cover';
        }

        media.style.maxWidth = '100px';
        media.style.maxHeight = '100px';

        const fileName = document.createElement('span');
        fileName.textContent = file.name.length > 15 ?
            file.name.substring(0, 12) + '...' : file.name;
        fileName.style.fontSize = '12px';
        fileName.style.marginTop = '5px';

        const removeBtn = document.createElement('button');
        removeBtn.innerHTML = '×';
        removeBtn.style.position = 'absolute';
        removeBtn.style.top = '-10px';
        removeBtn.style.right = '-10px';
        removeBtn.style.background = 'transparent';
        removeBtn.style.color = 'var(--cor-texto)';
        removeBtn.style.border = 'none';
        removeBtn.style.width = '20px';
        removeBtn.style.height = '20px';
        removeBtn.style.cursor = 'pointer';
        removeBtn.style.padding = '0';
        removeBtn.style.display = 'flex';
        removeBtn.style.justifyContent = 'center';
        removeBtn.style.alignItems = 'center';
        removeBtn.style.fontSize = '14px';

        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            removeFile(index);
        });

        previewItem.appendChild(media);
        previewItem.appendChild(fileName);
        previewItem.appendChild(removeBtn);
        uploadList.appendChild(previewItem);
    }

    function removeFile(index) {
        selectedFiles.splice(index, 1);
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
});
