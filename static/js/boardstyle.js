const themeSelector = document.getElementById('theme-selector');

const savedTheme = sessionStorage.getItem('selectedTheme');
if (savedTheme) {
    const existingLink = document.createElement('link');
    existingLink.rel = 'stylesheet';
    existingLink.href = savedTheme;
    document.head.appendChild(existingLink);
}

themeSelector.addEventListener('change', function() {
    const selectedStyle = this.value;

    if (selectedStyle) {
        sessionStorage.setItem('selectedTheme', selectedStyle);

        const existingLink = document.querySelector('link[rel="stylesheet"]');
        if (existingLink) {
            document.head.removeChild(existingLink);
        }

        const newLink = document.createElement('link');
        newLink.rel = 'stylesheet';
        newLink.href = selectedStyle;
        document.head.appendChild(newLink);
    }
});