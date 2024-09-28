document.getElementById('togglePostFormLink').addEventListener('click', function(event) {
    event.preventDefault();
    var formDiv = document.querySelector('.newboard-form');
    formDiv.style.display = formDiv.style.display === 'none'? 'block' : 'none';

});

const draggableForm = document.getElementById('draggableForm');

draggableForm.addEventListener('mousedown', function(e) {
    let shiftX = e.clientX - draggableForm.getBoundingClientRect().left;
    let shiftY = e.clientY - draggableForm.getBoundingClientRect().top;

    function moveAt(pageX, pageY) {
        draggableForm.style.left = pageX - shiftX + 'px';
        draggableForm.style.top = pageY - shiftY + 'px';
    }

    function onMouseMove(e) {
        moveAt(e.pageX, e.pageY);
    }

    document.addEventListener('mousemove', onMouseMove);

    function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp); 
    }

    document.addEventListener('mouseup', onMouseUp);
});

draggableForm.ondragstart = function() {
    return false;
};
