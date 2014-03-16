$(document).ready(function() {
    Admin.enableTriggers();
});

// ------------------------------------------------------------------------- //

var Admin = function() {
    var elements = {
        adminContent: "div.adminContent",
        refreshMedia: "div.refreshMedia",
        showSnakes: "div.showSnakes"
    };

    // --------------------------------------------------------------------- //

    var refreshMedia = function() {
        $.get(shared.api + "/index");
    };

    var showSnakes = function() {
        var url = shared.api + "/snakes";

        $.get(url, function(data) {
            var snakes = data["snakes"];

            if (snakes.length === 0) {
                return;
            }

            var html = "<div class='boxFull'>";
            html += "<div class='" + shared.classes.mainContentsBox + "'>";

            for (var i = 0; i < snakes.length; i++) {
                var snake = snakes[i];
                html += "<div class='contentsButtonBox'>";
                html += "<div class='contentsButton'>";
                html += "<a href='/medusa/admin/" + snake + "'>" + snake + "</a>";
                html +=  "</div></div>";
            }

            html += "</div></div>";

            $(elements.adminContent).html(html);
        });
    };

    // --------------------------------------------------------------------- //

    return {
        enableTriggers: function() {
            $(elements.refreshMedia).click(function() {
                refreshMedia();
            });

            $(elements.showSnakes).click(function() {
                showSnakes();
            });
        }
    };
}();
