$(document).ready(function() {
    Media.enableTriggers();
});

// ------------------------------------------------------------------------- //

var Media = function() {
    var elements = {
        chooseSnake: "div.chooseSnake",
        startPlaying: "div.startPlaying"
    };

    // --------------------------------------------------------------------- //

    var enableKeyboardShortcuts = function() {
        $(document).keyup(function(event_) {
            switch (event_.which) {
                case 13:
                    triggerAction("start");
                    event_.preventDefault();
                    break;

                case 37:
                    triggerAction("previous");
                    event_.preventDefault();
                    break;

                case 39:
                    triggerAction("next");
                    event_.preventDefault();
                    break;
            }
        });
    };

    // --------------------------------------------------------------------- //

    var showSnakes = function(element) {
        var url = shared.api + "/snakes";
        var container = $("div.playQueueContainer");
        var queue = false;

        if ($.trim($(element).text()) == "Queue") {
            queue = true;
        }

        if (queue === true) {
            url += "/queue";
        }

        $.get(url, function(data) {
            var snakes = data["snakes"];

            var html = "";

            for (var i = 0; i < snakes.length; i++) {
                var snake = snakes[i];
                var playingClass = "startPlaying";

                if (i !== 0) {
                    html += Utilities.toHTML({
                        div: {
                            class: "buttonGap"
                        }
                    });
                }

                html += Utilities.toHTML({
                    div: {
                        class: [
                            shared.classes.contentsButton,
                            playingClass
                        ],
                        content: snake
                    }
                });
            }

            $(container).html(html);

            $(elements.startPlaying).click(function() {
                startPlaying(this, queue);
            });
        });
    };

    var startPlaying = function(element, queue) {
        var action = "play";

        if (queue === true) {
            action = "queue";
        }

        var snake = $(element).text();
        var bits = Utilities.getURLBits();
        var media_id = bits[3];

        if (media_id === "new") {
            media_id = bits[4];
        }

        var url = shared.api + "/snake/" + snake + "/" + action + "/" + media_id;

        $.get(url, function() {
            if (action === "queue") {
                window.location.reload();
            }
            else {
                window.location = "/medusa/playing/" + snake;
            }
        });
    };

    // --------------------------------------------------------------------- //

    var triggerAction = function(action) {
        if (action === "start") {
            if ($(elements.startPlaying).length > 0) {
                $($(elements.startPlaying)[0]).trigger("click");
            }
            else {
                $(elements.chooseSnake).trigger("click");
            }
        }
        else {
            var element = "a." + action + "Button";

            if ($(element).length > 0) {
                window.location = $(element).attr("href");
            }
        }
    };

    // --------------------------------------------------------------------- //

    return {
        enableTriggers: function() {
            $(elements.chooseSnake).click(function() {
                showSnakes(this);
            });

            enableKeyboardShortcuts();
        }
    };
}();
