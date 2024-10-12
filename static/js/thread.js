document.addEventListener("DOMContentLoaded", function() {
    var postContents = document.querySelectorAll('pre');
    postContents.forEach(function(postContent) {
        postContent.innerHTML = postContent.innerHTML.replace(/&gt;([^<&\n]+)/g, '<span class="verde">&gt;$1</span>');
        postContent.innerHTML = postContent.innerHTML.replace(/&lt;([^<&\n]+)/g, '<span class="vermelho">&lt;$1</span>');
        postContent.innerHTML = postContent.innerHTML.replace(/\(\(\(([^()]*?)\)\)\)/g, '<span class="detected">((( $1 )))</span>');
        postContent.innerHTML = postContent.innerHTML.replace(/==([^=]+)==/g, '<span class="red-text">$1</span>');
    });

});
function substituirSpoilers() {
    var pres = document.getElementsByTagName('pre');
    for (var i = 0; i < pres.length; i++) {
        var pre = pres[i];
        pre.innerHTML = pre.innerHTML.replace(/\[spoiler\](.*?)\[\/spoiler\]/g, '<span class="spoiler">$1</span>');
        pre.innerHTML = pre.innerHTML.replace(/\[r\](.*?)\[\/r\]/g, '<span class="rainbowtext">$1</span>');
    }
}
const textarea = document.getElementById('text');

let quoteButton;

    document.addEventListener('mouseup', () => {
        const selection = window.getSelection();
        if (selection.toString()) {
            if (!quoteButton) {
                quoteButton = document.createElement('button');
                quoteButton.className = 'quote-button';
                quoteButton.innerText = 'Quotar';
                document.body.appendChild(quoteButton); 
            }

            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();

            quoteButton.style.left = `${rect.left + window.scrollX}px`;
            quoteButton.style.top = `${rect.top + window.scrollY - 10}px`;

            requestAnimationFrame(() => {
                quoteButton.style.display = 'block'; 
            });
        } else if (quoteButton) {
            quoteButton.style.display = 'none'; 
        }
    });

    document.addEventListener('click', (e) => {
        if (quoteButton && e.target !== quoteButton) {
            quoteButton.style.display = 'none';
        }
    });

    document.addEventListener('click', (e) => {
        if (quoteButton && e.target === quoteButton) {
            const selection = window.getSelection();
            const selectedText = selection.toString();
            textarea.value += '>' + (textarea.value ? '\n' : '') + selectedText;
            quoteButton.style.display = 'none';
            window.getSelection().removeAllRanges();
        }
    });
window.onload = function() {
    substituirSpoilers();
};
