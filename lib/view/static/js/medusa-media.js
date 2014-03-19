$(document).ready(function() {
    Media.enableTriggers();
});

// ------------------------------------------------------------------------- //

var Media = function() {
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

            $("div.startPlaying").click(function() {
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

    return {
        enableTriggers: function() {
            $("div.chooseSnake").click(function() {
                showSnakes(this);
            });
        }
    };
}();
