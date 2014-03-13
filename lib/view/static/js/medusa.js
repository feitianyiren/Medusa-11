var apiBase = "/medusa/api";

// ------------------------------------------------------------------------- //

$(document).ready(function() {
    checkPage();
});

// ------------------------------------------------------------------------- //

function checkPage() {
    var page = _getUrlBits()[2];
    if (page == "media") { page = "browse"; }

    $("div.menuButtonBox").each(function() {
        if ($(this).data("page") == page) {
            $(this).addClass("currentPage");
        }
    });
}

// ------------------------------------------------------------------------- //

function _getUrlBits() {
    return window.location.pathname.split("/");
}
