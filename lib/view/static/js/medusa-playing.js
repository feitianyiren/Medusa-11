var updateInterval = 1000;
var maxRetries = 3;
var retries = 0;
var snakeName = Utilities.getURLBits()[3];
var progressBar = "progress.progressBar";
var mediaId;
var timeTotal;
var audioTracks;
var subtitleTracks;

// ------------------------------------------------------------------------- //

$(document).ready(function() {
    var alternative = Utilities.getURLBits()[4];

    if (alternative) {
        enableAlternativeTriggers();

        if (alternative === "advanced") {
            enableAdvancedTriggers();
        }
        else if (alternative === "navigation") {
            enableNavigationKeyboardShortcuts();
        }
    }
    else {
        enableBasicTriggers();

        enableKeyboardShortcuts();
    }

    beginMediaUpdating();
});

// ------------------------------------------------------------------------- //

function enableBasicTriggers() {
    $("a.advancedOptions").prop("href", window.location.pathname + "/advanced");
    $("a.navigationOptions").prop("href", window.location.pathname + "/navigation");

    $("div." + shared.classes.contentsButton).click(function() {
        triggerAction($(this).data("action"), $(this).data("value"));
    });

    $(progressBar + ", div.progressBarText").click(function(event_) {
        clickProgressBar(event_, this);
    });
}

function enableAlternativeTriggers() {
    var basicLink = window.location.pathname.split("/").slice(0, 4).join("/");
    $("a.basicOptions").prop("href", basicLink);

    $(document).keyup(function(event_) {
        if (event_.which == 27) {
            window.location = basicLink;
        }
    });
}

function enableAdvancedTriggers() {
    $("div.buttonSubtitles").click(function() {
        showTracks("subtitle");
    });

    $("div.buttonAudio").click(function() {
        showTracks("audio");
    });
}

function beginMediaUpdating() {
    updateMedia(true);

    setInterval(function() {
        updateMedia();
    }, updateInterval);
}

function enableKeyboardShortcuts() {
    $(document).keyup(function(event_) {
        switch (event_.which) {
            case 32:
                triggerAction("pause");
                event_.preventDefault();
                break;

            case 37:
                triggerAction("jump_backward");
                event_.preventDefault();
                break;

            case 38:
                triggerAction("volume_up");
                event_.preventDefault();
                break;

            case 39:
                triggerAction("jump_forward");
                event_.preventDefault();
                break;

            case 40:
                triggerAction("volume_down");
                event_.preventDefault();
                break;
        }
    });
}

function enableNavigationKeyboardShortcuts() {
    $(document).keyup(function(event_) {
        switch (event_.which) {
            case 13:
                triggerAction("navigate", "0");
                event_.preventDefault();
                break;

            case 37:
                triggerAction("navigate", "3");
                event_.preventDefault();
                break;

            case 38:
                triggerAction("navigate", "1");
                event_.preventDefault();
                break;

            case 39:
                triggerAction("navigate", "4");
                event_.preventDefault();
                break;

            case 40:
                triggerAction("navigate", "2");
                event_.preventDefault();
                break;
        }
    });
}

// ------------------------------------------------------------------------- //

function updateMedia(initialLoad) {
    $.get(shared.api + "/status/" + snakeName, function(data) {
        var state = data["state"];
        var timeElapsed = data["elapsed"];
        timeTotal = data["total"];

        var buttonPause = "div.buttonPause";

        if (state == "paused") {
            $(buttonPause).text("Resume");
        }
        else {
            $(buttonPause).text("Pause");
        }

        var buttonMute = "div.buttonMute";

        if (data["mute"]) {
            $(buttonMute).text("Unmute");
        }
        else {
            $(buttonMute).text("Mute");
        }

        if ((state == "opped") ||
            (state == "ended") ||
            (state == "nothingspecial") ||
            ((timeElapsed > 0) && (timeElapsed == timeTotal))) {
            if ((initialLoad) || (retries < maxRetries)) {
                retries += 1;
                return;
            }

            window.location = "/medusa";
        }

        if (data["media_id"] != mediaId) {
            mediaId = data["media_id"];
            audioTracks = data["audio"];
            subtitleTracks = data["subtitles"];

            if (isNaN(mediaId)) {
                _updateTextAlternative(data);
            }
            else {
                $.get(shared.api + "/media/" + mediaId, function(data) {
                    _updateText(data);
                });
            }
        }

        _moveProgressBar(timeElapsed / timeTotal);
        var elapsed = _formatTime(timeElapsed);
        var total = _formatTime(timeTotal);

        if (elapsed != "aN:aN") {
            $("div.progressBarText").html(elapsed + " / " + total);
        }
    });
}

function triggerAction(action, value, reload) {
    if (value === 0) {
        value = "0";
    }

    var url = shared.api + "/snake/" + snakeName + "/" + action;

    if (value) {
        url += "/" + value;
    }

    $.get(url, function() {
        if (reload) {
            window.location.reload();
        }

        if (action == "stop") {
            window.location = "/medusa/browse";
        }
    });
}

function clickProgressBar(event_, element) {
    if (!timeTotal) { return; }

    var barWidth = $(progressBar).css("width").slice(0, -2);
    var clickPosition = event_.pageX - element.offsetLeft;
    var percentage = clickPosition / barWidth;

    triggerAction("jump_to", Math.round(percentage * timeTotal));
}

function showTracks(type) {
    _toggleAdvancedOptions();

    if (type == "subtitle") {
        tracks = subtitleTracks;
    }
    else {
        tracks = audioTracks;
    }

    var html = "";
    html += "<div class='boxFull'>";

    if (tracks.length === 0) {
        tracks.push([-1, "Disable"]);
    }

    for (var i = 0; i < tracks.length; i++) {
        var track = tracks[i];
        html += "<div class='" + shared.classes.mainContentsBox + "'>";
        html += "<div class='" + shared.classes.contentsButtonBox + "'>";
        html += "<div class='" + shared.classes.contentsButton + " changeTrack'";
        html += " data-type='" + type + "'";
        html += " data-track='" + track[0] + "'>";
        html += track[1];
        html += "</div>";
        html += "</div>";
        html += "</div>";
    }

    html += "</div>";

    $("div.advancedContent").replaceWith(html);

    $("div.changeTrack").click(function() {
        _changeTrack(this);
    });
}

// ------------------------------------------------------------------------- //

function _updateTextAlternative(data) {
    if (data["media_id"] == "disc") {
        $("div.navigationOptionsBox").show();
    }

    $("div.textTitle").html(data["name"]);
    $("div.textSubTitle").hide();
}

function _updateText(data) {
    var textTitle;
    var textSubTitle;
    var textRight;
    var category = data["category"].toLowerCase();
    
    if (category == "television") {
        var season = ("0" + data["name_two"]).slice(-2);
        var episode = ("0" + data["name_three"]).slice(-2);
        var showUrl = "/medusa/browse/television/" + data["name_one"];

        textTitle = data["name_four"];
        textSubTitle = "<a href=\"" + showUrl + "\">";
        textSubTitle += data["name_one"];
        textSubTitle += "</a>";
        textRight = "<a href=\"" + showUrl + "/" + data["name_two"] + "\">";
        textRight += "S" + season + "E" + episode;
        textRight += "</a>";
    }
    else {
        if (category == "film") {
            var imdb = "http://www.imdb.com/find?q=" + data["name_one"] + "#tt";
            textTitle = "<a href='" + imdb + "' target='_blank'>";
            textTitle += data["name_one"] + "</a>";
        }
        else {
            textTitle = data["name_one"];
        }

        textSubTitle = data["name_two"].join(", ");
        textRight = data["year"];
    }

    htmlRight = "<div class='" + shared.classes.floatRight + "'>" + textRight + "</div>";

    $("div.textTitle").html(textTitle);
    $("div.textSubTitle").html(textSubTitle);
    $("div.textSubTitle").append(htmlRight);
    $("div.textSubTitle").show();
}

function _toggleAdvancedOptions() {
    var basic = $("div.basicOptions");
    var advanced = $("div.advancedOptions");

    if (basic.length !== 0) {
        $(basic).text("Advanced Options");
        $(basic).prop("href", window.location.pathname);
    }
    else {
        $(advanced).text("Basic Options");
    }
}

function _changeTrack(element) {
    var trackType = $(element).data("type");
    var trackID = $(element).data("track");

    triggerAction(trackType, trackID, true);
}

function _moveProgressBar(percentage) {
    var progressMax = $(progressBar).attr("max");
    var newWidth = progressMax * percentage;

    $(progressBar).attr("value", newWidth);
}

function _formatTime(time) {
    var hours = Math.floor(time / 3600);
    time = time - hours * 3600;
    var minutes = ("0" + Math.floor(time / 60)).slice(-2);
    var seconds = ("0" + (time - (minutes * 60))).slice(-2);
    var timeString = "";

    if (hours > 0) {
        timeString += hours + ":";
    }

    return timeString + minutes + ":" + seconds;
}
