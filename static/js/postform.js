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
        draggableForm.style.left = pageX - shiftX + 'px';
        draggableForm.style.top = pageY - shiftY + 'px';
    }

    function onMouseMove(e) {
        if (!isDragging) {
            isDragging = true;
            moveAt(e.pageX, e.pageY);
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
