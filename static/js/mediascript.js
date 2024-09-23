var postImgs = document.querySelectorAll('.post_img');

postImgs.forEach(function(img) {
    img.addEventListener('click', function() {
        var isExpanded = img.dataset.expanded === 'true';

        if (isExpanded) {
            img.style.width = '';
            img.style.height = '';
            img.dataset.expanded = 'false';
        } else {
            img.style.width = 'fit-content';
            img.style.height = 'fit-content';
            img.dataset.expanded = 'true';
        }
    });
});