var shared = {
    classes: {
        contentsButton: "contentsButton",
        contentsButtonBox: "contentsButtonBox",
        boxFull: "boxFull",
        floatRight: "floatRight",
        mainContentsBox: "mainContentsBox"
    },
    api: "/medusa/api"
};

// ------------------------------------------------------------------------- //

$(document).ready(function() {
    Utilities.setPage();
});

// ------------------------------------------------------------------------- //

var Utilities = function() {
    return {
        getURLBits: function() {
            return window.location.pathname.split("/");
        },

        setPage: function() {
            var page = Utilities.getURLBits()[2];
            if (page == "media") {
                page = "browse";
            }

            $("div.menuButtonBox").each(function() {
                if ($(this).data("page") == page) {
                    $(this).addClass("currentPage");
                }
            });
        },

        formatTime: function(time) {
            var hours = Math.floor(time / 3600);
            time = time - hours * 3600;
            var minutes = ("0" + Math.floor(time / 60)).slice(-2);
            var seconds = ("0" + (time - (minutes * 60))).slice(-2);
            var timeString = "";

            if (hours > 0) {
                timeString += hours + ":";
            }

            return timeString + minutes + ":" + seconds;
        },

        toHTML: function(elements) {
            var content = "content";
            var children = "children";
            var childrenBefore = "childrenBefore";
            var close = "close";

            var safeProperties = [
                content,
                children,
                childrenBefore,
                close
            ];

            var buildProperty = function(name, value) {
                if (value === true) {
                    return " " + name;
                }

                var property = "";

                property += " " + name + "=\"";
                property += value.toString().replace("\"", "'");
                property += "\"";

                return property;
            };

            if ($.type(elements) !== "array") {
                elements = [elements];
            }

            var html = "";

            for (var i = 0; i < elements.length; i++) {
                var structure = elements[i];

                for (var kind in structure) {
                    var properties = structure[kind];

                    html += "<" + kind;

                    for (var name in properties) {
                        if ($.inArray(name, safeProperties) !== -1) {
                            continue;
                        }

                        var value = properties[name];

                        if ($.type(value) === "object") {
                            for (var subProperty in value) {
                                html += buildProperty(name + "-" + subProperty,
                                                      value[subProperty]);
                            }
                        }
                        else {
                            if ($.type(value) === "array") {
                                value = value.join(" ");
                            }

                            html += buildProperty(name, value);
                        }
                    }

                    html += ">";

                    if ((properties[childrenBefore] === true) &&
                        (properties[children])) {
                        html += Utilities.toHTML(properties[children]);
                    }

                    if (properties[content]) {
                        html += properties[content];
                    }

                    if ((properties[childrenBefore] !== true) &&
                        (properties[children])) {
                        if (properties[children]) {
                            html += Utilities.toHTML(properties[children]);
                        }
                    }

                    if (properties[close] !== false) {
                        html += "</" + kind + ">";
                    }
                }
            }

            return html;
        }
    };
}();
