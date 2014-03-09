$(document).ready(function() {
    checkLocation();

    $(".browseMedia").click(function() {
        $(".browseMenuBox").hide();
        $(".browseCategoriesBox").show();
    });

    $(".searchInput").keyup(function() {
        doSearch(this);
    });
});

// ------------------------------------------------------------------------- //

function checkLocation() {
    var bits = _getUrlBits();

    if ((bits[2] == "television") && (bits.length == 4)) {
        var button = "#titleBrowse";
        var link = $(button).closest("a");

        $(button).text("Television");
        $(link).attr("href", "/medusa/browse/television");
    }
}

function doSearch(element) {
    var term = $(element).val();

    if (term.length < 2) {
        $(".searchResults").hide();
        $(".menuItems").show();
        return;
    }
    else {
        $(".searchResults").show();
        $(".menuItems").hide();
    }

    $.post(apiBase + "/search", {"term": term}, function(data) {
        data = data["media"];
        var items = "";

        for (var i = 0; i < data.length; i++) {
            var media = data[i];
            var item = "";
            var category = media["category"].toLowerCase();

            if (category == "film") {
                item = _buildFilmResult(media["id"], media);
            }
            else if (category == "television") {
                item = _buildEpisodeResult(media["id"], media);
            }

            items += item;
        }

        $(".searchResults").html(items);
    });
}

// ------------------------------------------------------------------------- //

function _buildFilmResult(key, data) {
    var item = "<a class='mainContentsBox contentsLink'";
    item += " href='/medusa/media/" + key + "'>";
    item += "<div class='contentsText contentsName'>";
    item += data["name_one"];
    item += "</div>";
    item += "<div class='contentsYear floatRight'>";
    item += data["year"];
    item += "</div>";
    item += "</a>";

    return item;
}

function _buildEpisodeResult(key, data) {
    var season = ("0" + data["name_two"]).slice(-2);
    var episode = ("0" + data["name_three"]).slice(-2);

    var name = data["name_one"] + " - S" + season + "E" + episode;
    name += " - " + data["name_four"];

    var item = "<a class='mainContentsBox contentsLink'";
    item += " href='/medusa/media/" + key + "'>";
    item += "<div class='contentsText contentsName'>";
    item += name;
    item += "</div>";
    item += "</a>";

    return item;
}