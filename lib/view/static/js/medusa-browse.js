$(document).ready(function() {
    Browse.tweakLocation();

    $("div.browseMedia").click(function() {
        $("div.browseMenuBox").hide();
        $("div.browseCategoriesBox").show();
    });

    $("input.searchInput").keyup(function() {
        Browse.search(this);
    });
});

// ------------------------------------------------------------------------- //

var Browse = function() {
    var classes = {
        contentsLink: "contentsLink",
        contentsName: "contentsName",
        contentsText: "contentsText"
    };

    var elements = {
        menuItems: "div.menuItems",
        searchResults: "div.searchResults"
    };

    // --------------------------------------------------------------------- //

    var buildFilmResult = function(key, data) {
        return Utilities.toHTML({
            a: {
                class: [
                    shared.classes.mainContentsBox,
                    classes.contentsLink
                ],
                href: "/medusa/media/" + key,
                children: [
                    {
                        div: {
                            class: [
                                classes.contentsText,
                                classes.contentsName
                            ],
                            content: data["name_one"]
                        }
                    },
                    {
                        div: {
                            class: [
                                "contentsYear",
                                shared.classes.floatRight
                            ],
                            content: data["year"]
                        }
                    }
                ]
            }
        });
    };

    var buildEpisodeResult = function(key, data) {
        var season = ("0" + data["name_two"]).slice(-2);
        var episode = ("0" + data["name_three"]).slice(-2);

        var name = data["name_one"] + " - S" + season + "E" + episode;
        name += " - " + data["name_four"];

        return Utilities.toHTML({
            a: {
                class: [
                    shared.classes.mainContentsBox,
                    classes.contentsLink
                ],
                href: "/medusa/media/" + key,
                children: {
                    div: {
                        class: [
                            classes.contentsText,
                            classes.contentsName
                        ],
                        content: name
                    }
                }
            }
        });
    };

    var buildTrackResult = function(key, data) {
        var name = data["name_one"] + " - " + data["name_two"];
        name += " - " + data["name_three"];

        return Utilities.toHTML({
            a: {
                class: [
                    shared.classes.mainContentsBox,
                    classes.contentsLink
                ],
                href: "/medusa/media/" + key,
                children: {
                    div: {
                        class: [
                            classes.contentsText,
                            classes.contentsName
                        ],
                        content: name
                    }
                }
            }
        });
    };

    // --------------------------------------------------------------------- //

    return {
        tweakLocation: function() {
            var bits = Utilities.getURLBits();

            if (bits.length === 5) {
                var button = "div#titleBrowse";
                var link = $(button).closest("a");

                if (bits[3] === "television") {
                    $(button).text("Television");
                    $(link).attr("href", "/medusa/browse/television");
                }
                else if (bits[3] === "music") {
                    $(button).text("Music");
                    $(link).attr("href", "/medusa/browse/music");
                }
            }
        },

        search: function(element) {
            var term = $(element).val();

            if (term.length < 2) {
                $(elements.searchResults).hide();
                $(elements.menuItems).show();
                return;
            }
            else {
                $(elements.searchResults).show();
                $(elements.menuItems).hide();
            }

            $.post(shared.api + "/search", {"term": term}, function(data) {
                data = data["media"];
                var items = "";

                for (var i = 0; i < data.length; i++) {
                    var media = data[i];
                    var item = "";
                    var category = media["category"].toLowerCase();

                    if (category === "film") {
                        item = buildFilmResult(media["id"], media);
                    }
                    else if (category === "television") {
                        item = buildEpisodeResult(media["id"], media);
                    }
                    else if (category === "music") {
                        item = buildTrackResult(media["id"], media);
                    }

                    items += item;
                }

                $(elements.searchResults).html(items);
            });
        }
    };
}();
