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
zoomedImage.style.maxWidth = '300px';
zoomedImage.style.maxHeight = '300px';
zoomedImage.style.zIndex = '990';

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

  const windowWidth = window.innerWidth;
  const windowHeight = window.innerHeight;

  let newX = event.pageX + offsetX;
  let newY = event.pageY + offsetY;

  if (newX + zoomedImage.clientWidth > windowWidth + window.scrollX) {
    newX = windowWidth + window.scrollX - zoomedImage.clientWidth - offsetX;
  }
  if (newY + zoomedImage.clientHeight > windowHeight + window.scrollY) {
    newY = windowHeight + window.scrollY - zoomedImage.clientHeight - offsetY;
  }

  zoomedImage.style.top = newY + 'px';
  zoomedImage.style.left = newX + 'px';
}
