$(document).ready(function() {
    var alternative = Utilities.getURLBits()[4];

    if (alternative) {
        Playing.enableAlternativeTriggers();

        if (alternative === "advanced") {
            Playing.enableAdvancedTriggers();
        }
        else if (alternative === "navigation") {
            Playing.enableNavigationKeyboardShortcuts();
        }
    }
    else {
        Playing.enableBasicTriggers();
        Playing.enableBasicKeyboardShortcuts();
    }

    Playing.beginUpdating();
});

// ------------------------------------------------------------------------- //

var Playing = function() {
    var audioTracks;
    var maxRetries = 3;
    var mediaId;
    var pathname = window.location.pathname;
    var retries = 0;
    var snakeName = Utilities.getURLBits()[3];
    var subtitleTracks;
    var timeTotal;
    var updateInterval = 1000;

    // --------------------------------------------------------------------- //

    var classes = {
        buttonClicked: "buttonClicked",
        buttonClickedFinish: "buttonClickedFinish"
    };

    var elements = {
        advancedOptions: "a.advancedOptions",
        progressBar: "progress.progressBar",
        progressBarText: "div.progressBarText",
        textTitle: "div.textTitle",
        textSubTitle: "div.textSubTitle"
    };

    // --------------------------------------------------------------------- //

    var updateMedia = function(initialLoad) {
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
                    updateTextAlternative(data);
                }
                else {
                    $.get(shared.api + "/media/" + mediaId, function(data) {
                        updateTextBasic(data);
                    });
                }
            }

            moveProgressBar(timeElapsed / timeTotal);
            var elapsed = Utilities.formatTime(timeElapsed);
            var total = Utilities.formatTime(timeTotal);

            if (elapsed != "aN:aN") {
                $(elements.progressBarText).html(elapsed + " / " + total);
            }
        });
    };

    // --------------------------------------------------------------------- //

    var enableActionButtons = function() {
        $("div." + shared.classes.contentsButton).click(function() {
            animateClick(this);
            triggerAction($(this).data("action"), $(this).data("value"));
        });
    };

    var triggerAction = function(action, value, reload) {
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
    };

    var animateClick = function(element) {
        $(element).removeClass(classes.buttonClickedFinish);
        $(element).addClass(classes.buttonClicked);

        setTimeout(function() {
            $(element).addClass(classes.buttonClickedFinish);
            $(element).removeClass(classes.buttonClicked);
        }, 750);
    };

    // --------------------------------------------------------------------- //

    var clickProgressBar = function(event_, element) {
        if (!timeTotal) {
            return;
        }

        var barWidth = $(elements.progressBar).css("width").slice(0, -2);
        var clickPosition = event_.pageX - element.offsetLeft;
        var percentage = clickPosition / barWidth;

        triggerAction("jump_to", Math.round(percentage * timeTotal));
    };

    var changeTrack = function(element) {
        var trackType = $(element).data("type");
        var trackID = $(element).data("track");

        triggerAction(trackType, trackID, true);
    };

    // --------------------------------------------------------------------- //

    var showTracks = function(type) {
        toggleAdvancedOptions();

        if (type == "subtitle") {
            tracks = subtitleTracks;
        }
        else {
            tracks = audioTracks;
        }

        if (tracks.length === 0) {
            tracks.push([-1, "Disable"]);
        }

        var content = "";

        for (var i = 0; i < tracks.length; i++) {
            var track = tracks[i];

            content += Utilities.toHTML({
                div: {
                    class: shared.classes.mainContentsBox,
                    children: {
                        div: {
                            class: shared.classes.contentsButtonBox,
                            children: {
                                div: {
                                    class: [
                                        shared.classes.contentsButton,
                                        "changeTrack"
                                    ],
                                    data: {
                                        type: type,
                                        track: track[0]
                                    },
                                    content: track[1]
                                }
                            }
                        }
                    }
                }
            });
        }

        html = Utilities.toHTML({
            div: {
                class: shared.classes.boxFull,
                content: content
            }
        });

        $("div.advancedContent").replaceWith(html);

        $("div.changeTrack").click(function() {
            changeTrack(this);
        });
    };

    // --------------------------------------------------------------------- //

    var updateTextBasic = function(data) {
        var textTitle;
        var textSubTitle;
        var textRight;
        var category = data["category"].toLowerCase();

        $(elements.advancedOptions).parent().show();

        if (category === "television") {
            var season = ("0" + data["name_two"]).slice(-2);
            var episode = ("0" + data["name_three"]).slice(-2);
            var showUrl = "/medusa/browse/television/" + data["name_one"];

            textTitle = data["name_four"];

            textSubTitle = Utilities.toHTML({
                a: {
                    href: showUrl,
                    content: data["name_one"]
                }
            });

            textRight = Utilities.toHTML({
                a: {
                    href: showUrl + "/" + data["name_two"],
                    content: "S" + season + "E" + episode
                }
            });
        }
        else if (category === "music") {
            textTitle = data["name_three"];

            textSubTitle = Utilities.toHTML({
                a: {
                    href: "/medusa/browse/music/" + data["name_one"] + "/" + data["name_two"],
                    content: data["name_two"]
                }
            });

            textRight = Utilities.toHTML({
                a: {
                    href: "/medusa/browse/music/" + data["name_one"],
                    content: data["name_one"]
                }
            });

            $(elements.advancedOptions).parent().hide();
        }
        else {
            if (category == "film") {
                var imdb = "http://www.imdb.com/find?q=" + data["name_one"] + "#tt";

                textTitle = Utilities.toHTML({
                    a: {
                        href: imdb,
                        target: "_blank",
                        content: data["name_one"]
                    }
                });
            }
            else {
                textTitle = data["name_one"];
            }

            textSubTitle = data["name_two"].join(", ");
            textRight = data["year"];
        }

        htmlRight = Utilities.toHTML({
            div: {
                class: shared.classes.floatRight,
                content: textRight
            }
        });

        $(elements.textTitle).html(textTitle);
        $(elements.textSubTitle).html(textSubTitle);
        $(elements.textSubTitle).append(htmlRight);
        $(elements.textSubTitle).show();
    };

    var updateTextAlternative = function(data) {
        if (data["media_id"] == "disc") {
            $("div.navigationOptionsBox").show();
        }

        $(elements.textTitle).html(data["name"]);
        $(elements.textSubTitle).hide();
    };

    // --------------------------------------------------------------------- //

    var toggleAdvancedOptions = function() {
        var basic = $("div.basicOptions");
        var advanced = $("div.advancedOptions");

        if (basic.length !== 0) {
            $(basic).text("Advanced Options");
            $(basic).prop("href", pathname);
        }
        else {
            $(advanced).text("Basic Options");
        }
    };

    // --------------------------------------------------------------------- //

    var moveProgressBar = function(percentage) {
        var progressMax = $(elements.progressBar).attr("max");
        var newWidth = progressMax * percentage;

        $(elements.progressBar).attr("value", newWidth);
    };

    // --------------------------------------------------------------------- //

    return {
        enableBasicTriggers: function() {
            $(elements.advancedOptions).prop("href", pathname + "/advanced");
            $("a.navigationOptions").prop("href", pathname + "/navigation");

            enableActionButtons();

            $(elements.progressBar + ", " + elements.progressBarText).click(function(event_) {
                clickProgressBar(event_, this);
            });
        },

        enableAlternativeTriggers: function() {
            var basicLink = pathname.split("/").slice(0, 4).join("/");
            $("a.basicOptions").prop("href", basicLink);

            enableActionButtons();

            $(document).keyup(function(event_) {
                if (event_.which == 27) {
                    window.location = basicLink;
                }
            });
        },

        enableAdvancedTriggers: function() {
            $("div.buttonSubtitles").click(function() {
                showTracks("subtitle");
            });

            $("div.buttonAudio").click(function() {
                showTracks("audio");
            });
        },

        // ----------------------------------------------------------------- //

        enableBasicKeyboardShortcuts: function() {
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
        },

        enableNavigationKeyboardShortcuts: function() {
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
        },

        // ----------------------------------------------------------------- //

        beginUpdating: function() {
            updateMedia(true);

            setInterval(function() {
                updateMedia();
            }, updateInterval);
        }
    };
}();
