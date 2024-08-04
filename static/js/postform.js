document.getElementById('togglePostFormLink').addEventListener('click', function(event) {
    event.preventDefault();
    var formDiv = document.querySelector('.newboard-form');
    formDiv.style.display = formDiv.style.display === 'none'? 'block' : 'none';
    
    if (formDiv.style.display === 'block') {
        document.getElementById('togglePostFormLink').style.display = 'none';
    }
});