var jQuery = jQuery.noConflict();
var socket = io()

const notification_path = '/static/audios/notification.mp3';
const notification = new Audio(notification_path);

socket.on('nova_postagem', function(postagem) {
    notification.play();
    atualizarDiv();
});

var urlAtual = window.location.href;

function atualizarDiv() {
    $.ajax({
        url: urlAtual,
        success: function(data) {
            $('#posts_board').html($(data).find('#posts_board').html());
        }
    });
}