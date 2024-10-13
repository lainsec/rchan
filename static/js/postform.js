document.getElementById('togglePostFormLink').addEventListener('click', function(event) {
    event.preventDefault();
    
    var formDiv = document.querySelector('.newboard-form');
    
    if (formDiv.style.display === 'none') {
        formDiv.style.display = 'block';
        formDiv.style.position = 'absolute'; 
        formDiv.style.left = event.pageX + 'px'; 
        formDiv.style.top = (event.pageY + 10) + 'px'; 
    } else {
        formDiv.style.display = 'none'; 
    }
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
        // Calcula as novas posições
        let newLeft = pageX - shiftX;
        let newTop = pageY - shiftY;

        // Verifica os limites da janela
        const rightEdge = window.innerWidth - draggableForm.offsetWidth;
        const bottomEdge = window.innerHeight - draggableForm.offsetHeight;

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
