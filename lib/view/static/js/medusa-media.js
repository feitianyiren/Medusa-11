$(document).ready(function() {
    enableTriggers();
});

// ------------------------------------------------------------------------- //

function enableTriggers() {
    $(".chooseSnake").click(function() { showSnakes(this); });
}

// ------------------------------------------------------------------------- //

function showSnakes(element) {
    var url = apiBase + "/snakes";
    var container = $(".playQueueContainer");
    var queue = false;

    if ($.trim($(element).text()) == "Queue") {
        queue = true;
    }

    if (queue === true) {
        url += "/queue";
    }

    $.get(url, function(data) {
        var snakes = data["snakes"];

        if (queue === false) {
            snakes.push("Browser");
        }

        var html = "";

        for (var i = 0; i < snakes.length; i++) {
            var snake = snakes[i];
            var playingClass = "startPlaying";

            if (i !== 0) {
                html += "<div class='buttonGap'></div>";
            }

            if (snake == "Browser") {
                playingClass = "startBrowser";
            }

            html += "<div class='contentsButton " + playingClass + "'>";
            html += snake;
            html += "</div>";
        }

        $(container).html(html);

        $(".startPlaying").click(function() {
            startPlaying(this, queue);
        });
    });
}

function startPlaying(element, queue) {
    var action = "play";

    if (queue === true) {
        action = "queue";
    }

    var snake = $(element).text();
    var bits = _getUrlBits();
    var media_id = bits[3];

    if (media_id == "new") {
        media_id = bits[4];
    }

    var url = apiBase + "/snake/" + snake + "/" + action + "/" + media_id;

    $.get(url, function() {
        if (action == "queue") {
            window.location.reload();
        }
        else {
            window.location = "/medusa/playing/" + snake;
        }
    });
}
