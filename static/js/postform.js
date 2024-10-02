document.getElementById('togglePostFormLink').addEventListener('click', function(event) {
    event.preventDefault();
    var formDiv = document.querySelector('.newboard-form');
    formDiv.style.display = formDiv.style.display === 'none'? 'block' : 'none';

});

const draggableForm = document.getElementById('draggableForm');
draggableForm.style.position = 'absolute';

draggableForm.addEventListener('mousedown', function(e) {
    
    let isDragging = false;
    let rect = draggableForm.getBoundingClientRect();
    let shiftX = e.clientX - rect.left;
    let shiftY = e.clientY - rect.top + window.scrollY; // Adicione window.scrollY aqui

    function moveAt(pageX, pageY) {
        draggableForm.style.left = pageX - shiftX + 'px';
        draggableForm.style.top = pageY - shiftY + 'px';
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
    };
});
