var jQuery = jQuery.noConflict();
var socket = io()

const notification_path = '/static/audios/tuturu.mp3';
const notification = new Audio(notification_path);

socket.on('nova_postagem', function(postagem) {
    notification.play();
    atualizarDiv();
});

function atualizarDiv() {
    $.ajax({
        url: '/{{ board_id }}',
        success: function(data) {
            $('#posts_board').html($(data).find('#posts_board').html());
        }
    });
}