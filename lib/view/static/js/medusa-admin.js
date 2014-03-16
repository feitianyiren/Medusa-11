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

            var content = "";

            for (var i = 0; i < snakes.length; i++) {
                var snake = snakes[i];

                content += Utilities.toHTML({
                    div: {
                        class: shared.classes.contentsButtonBox,
                        children: {
                            div: {
                                class: shared.classes.contentsButton,
                                children: {
                                    a: {
                                        content: snake,
                                        href: "/medusa/admin/" + snake
                                    }
                                }
                            }
                        }
                    }
                });
            }

            html = Utilities.toHTML({
                div: {
                    class: "boxFull",
                    children: {
                        div: {
                            class: shared.classes.mainContentsBox,
                            content: content
                        }
                    }
                }
            });

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
