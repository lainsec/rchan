const button = document.getElementById('waring-button');
const div = document.getElementById('waring-container');
if (button && div) {
  button.addEventListener('click', () => {
    div.style.display = 'none';
  });
}
