$(document).ready(function() {
    $(".refreshMedia").click(function() {
        refreshMedia();
    });

    $(".showSnakes").click(function() {
        showSnakes();
    });
});

// ------------------------------------------------------------------------- //

function refreshMedia() {
    $.get(apiBase + "/index");
}

function showSnakes() {
    var url = apiBase + "/snakes";

    $.get(url, function(data) {
        var snakes = data["snakes"];
        if (snakes.length === 0) { return ; }

        var html = "<div class='boxFull'>";
        html += "<div class='mainContentsBox'>";

        for (var i = 0; i < snakes.length; i++) {
            var snake = snakes[i];
            html += "<div class='contentsButtonBox'>";
            html += "<div class='contentsButton'>";
            html += "<a href='/medusa/admin/" + snake + "'>" + snake + "</a>";
            html +=  "</div></div>";
        }

        html += "</div></div>";

        $(".adminContent").html(html);
    });
}
