document.addEventListener("DOMContentLoaded", function() {
    var postContents = document.querySelectorAll('.post_content pre');
    postContents.forEach(function(postContent) {
        postContent.innerHTML = postContent.innerHTML.replace(/&gt;([^<&\n]+)/g, '<span class="verde">&gt;$1</span>')
        postContent.innerHTML = postContent.innerHTML.replace(/&lt;([^<&\n]+)/g, '<span class="vermelho">&lt;$1</span>');
    });
    var replyContents = document.querySelectorAll('.reply_content pre');
    replyContents.forEach(function(replyContent) {
        replyContent.innerHTML = replyContent.innerHTML.replace(/&gt;([^<&\n]+)/g, '<span class="verde">&gt;$1</span>');
        replyContent.innerHTML = replyContent.innerHTML.replace(/&lt;([^<&\n]+)/g, '<span class="vermelho">&lt;$1</span>');
        replyContent.innerHTML = replyContent.innerHTML.replace(/(?:^|\s)(#[^\s<\n]+)/g, ' <a class="vermelho-reply" href="#" style="text-decoration: none;">$1</a>');
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
window.onload = function() {
    substituirSpoilers();
};