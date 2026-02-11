function refreshCaptcha(btn) {
    const container = btn.closest('.captcha-container');
    const img = container.querySelector('img');
    const icon = btn.querySelector('i');
    
    // Add rotation effect
    icon.classList.add('fa-spin');
    
    // Disable button to prevent double clicks
    btn.disabled = true;

    fetch('/api/refresh_captcha')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.captcha_image) {
                img.src = data.captcha_image;
            }
        })
        .catch(error => {
            console.error('Error refreshing captcha:', error);
            alert('Failed to refresh captcha. Please try again.');
        })
        .finally(() => {
            // Remove rotation effect and enable button
            icon.classList.remove('fa-spin');
            btn.disabled = false;
        });
}