const images = document.querySelectorAll('.post_img, .reply_img');

images.forEach(image => {
    if (image.id === "post_video_thumbnail") {
        return;
    }

    image.addEventListener('click', function() {
        this.style.display = 'none';

        const newImage = document.createElement('img');
        newImage.classList = "post_img_resized";
        newImage.src = this.src;
        newImage.alt = this.alt;
        newImage.style.cursor = 'pointer';

        this.parentNode.insertBefore(newImage, this.nextSibling);

        newImage.addEventListener('click', function() {
            this.remove();
            image.style.display = '';
        });
    });
});
