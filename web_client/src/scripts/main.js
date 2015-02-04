'use strict';

$(function() {

    var now = function() {
        var date = new Date();
        var time = date.getTime() - date.getTimezoneOffset() * 60 * 1000;
        return new Date(time).toISOString().slice(0, 19).replace('T', ' ');
    };
    
    $('.pref-area .button').click(function() {
        var button = $(this);
        button.addClass('active');
        button.children().transition('pulse');
        button.siblings().removeClass('active');
    });

    var addChatAreaMessage = function(message) {
        var header = $('<div>').addClass('header')
                               .text('发送消息 ' + now());

        var description = $('<div>').addClass('description')
                               .css('font-size', String(message.size) + 'px')
                               .text(message.text);
        if (message.color !== '#FFFFFF') {
            description.css('color', message.color);
        }

        var item = $('<div>').addClass('item user');
        item.append(header).append(description);
        item.prependTo('#chat-area > .list').hide().show('fast');
    };

    var getMessage = function() {
        var text = $('#input-area input').val().trim();
        if (!text) {
            return null;
        }

        var color = $('#color-group .button.active').data('value');
        var size = $('#size-group .button.active').data('value');
        var mode = $('#mode-group .button.active').data('value');
        var message = {
            text: text,
            color: color,
            size: parseInt(size),
            mode: parseInt(mode),
        };
        return message;
    };

    var sending = false;
    $('#input-area .button').click(function() {
        $(this).children().transition('pulse');

        if (sending) {
            return;
        }

        var message = getMessage();
        if (!message) {
            return;
        }

        $.post('/buibui/bui', message).done(function() {
            addChatAreaMessage(message);
            $('#input-area input').val('');
            $('#chat-area').animate({scrollTop: 0}, 200);
        });

    });

});
