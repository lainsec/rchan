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

        const existingThemeLink = document.querySelector('link.theme');
        if (existingThemeLink) {
            document.head.removeChild(existingThemeLink);
        }

        const newLink = document.createElement('link');
        newLink.rel = 'stylesheet';
        newLink.href = selectedStyle;
        newLink.className = 'theme'; 
        document.head.appendChild(newLink);

        location.reload();
    }
});
