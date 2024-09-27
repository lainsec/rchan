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

const postImages = document.querySelectorAll('img.post_img');
const zoomedImage = document.createElement('img');
zoomedImage.className = 'zoomed-image';
zoomedImage.style.position = 'absolute';
zoomedImage.style.display = 'none'; 

document.body.appendChild(zoomedImage);

postImages.forEach(image => {
  image.addEventListener('mouseover', function(event) {
    zoomedImage.src = image.src;
    zoomedImage.style.display = 'block'; 
    updateZoomedImagePosition(event);
  });

  image.addEventListener('mousemove', function(event) {
    updateZoomedImagePosition(event);
  });

  image.addEventListener('mouseout', function() {
    zoomedImage.style.display = 'none';
  });
});

function updateZoomedImagePosition(event) {
  const offsetX = 20; 
  const offsetY = 20; 
  zoomedImage.style.top = (event.clientY + offsetY) + 'px';
  zoomedImage.style.left = (event.clientX + offsetX) + 'px';
}
