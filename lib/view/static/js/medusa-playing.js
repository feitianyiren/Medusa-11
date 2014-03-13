var updateInterval = 1000;
var maxRetries = 3;
var retries = 0;
var snakeName = _getUrlBits()[3];
var progressBar = ".progressBar";
var mediaId;
var timeTotal;
var audioTracks;
var subtitleTracks;

// ------------------------------------------------------------------------- //

$(document).ready(function() {
    if (_getUrlBits()[4] == "advanced") {
        enableAdvancedTriggers();
    }
    else {
        enableBasicTriggers();
    }

    beginMediaUpdating();

    enableKeyboardShortcuts();
});

// ------------------------------------------------------------------------- //

function enableBasicTriggers() {
    $(".advancedOptions").prop("href", window.location.pathname + "/advanced");

    $(".contentsButton").click(function() {
        triggerAction($(this).data("action"));
    });

    $(progressBar + ", .progressBarText").click(function(event_) {
        clickProgressBar(event_, this);
    });
}

function enableAdvancedTriggers() {
    var advancedLink = window.location.pathname.replace("/advanced", "");
    $(".basicOptions").prop("href", advancedLink);

    $(".buttonSubtitles").click(function() {
        showTracks("subtitle");
    });

    $(".buttonAudio").click(function() {
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

// ------------------------------------------------------------------------- //

function updateMedia(initialLoad) {
    $.get(apiBase + "/status/" + snakeName, function(data) {
        var state = data["state"];
        var timeElapsed = data["elapsed"];
        timeTotal = data["total"];

        if (state == "paused") {
            $(".buttonPause").text("Resume");
        }
        else {
            $(".buttonPause").text("Pause");
        }

        if (data["mute"]) {
            $(".buttonMute").text("Unmute");
        }
        else {
            $(".buttonMute").text("Mute");
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
                _updateNewText(data);
            }
            else {
                $.get(apiBase + "/media/" + mediaId, function(data) {
                    _updateText(data);
                });
            }
        }

        _moveProgressBar(timeElapsed / timeTotal);
        var elapsed = _formatTime(timeElapsed);
        var total = _formatTime(timeTotal);

        if (elapsed != "aN:aN") {
            $(".progressBarText").html(elapsed + " / " + total);
        }
    });
}

function triggerAction(action, value, reload) {
    var url = apiBase + "/snake/" + snakeName + "/" + action;
    if (value) { url += "/" + value; }

    $.get(url, function() {
        if (reload) { window.location.reload(); }

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
        html += "<div class='mainContentsBox'>";
        html += "<div class='contentsButtonBox'>";
        html += "<div class='contentsButton changeTrack'";
        html += " data-type='" + type + "'";
        html += " data-track='" + track[0] + "'>";
        html += track[1];
        html += "</div>";
        html += "</div>";
        html += "</div>";
    }

    html += "</div>";

    $(".advancedContent").replaceWith(html);

    $(".changeTrack").click(function() {
        _changeTrack(this);
    });
}

// ------------------------------------------------------------------------- //

function _updateNewText(data) {
    $(".textTitle").html(data["media_id"]);
    $(".textSubTitle").hide();
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

    htmlRight = "<div class='floatRight'>" + textRight + "</div>";

    $(".textTitle").html(textTitle);
    $(".textSubTitle").html(textSubTitle);
    $(".textSubTitle").append(htmlRight);
    $(".textSubTitle").show();
}

function _toggleAdvancedOptions() {
    var basic = $(".basicOptions");
    var advanced = $(".advancedOptions");

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
