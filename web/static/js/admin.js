$(function() {
    var $menu = $("#menu-user-options");

    if (!$menu.length) {
        // Admin page: build the user options menu and wire up its click handler
        $menu = $("<ul />", { "id": "menu-user-options", "class": "menu" })
            .append($("<li />", { "class": "menu-sign-out" }).text("Sign out"));
        $("body").append($menu);

        $$menu.click(function(e) {
            if (e.$item.is(".menu-sign-out")) {
                $("#sign-out")[0].click();
            }
        });
    } else {
        // Reader page: prepend Administer to the existing menu and chain onto
        // reader.js's click handler to handle Administer clicks
        $menu.prepend(
            $("<li />", { "class": "menu-administer" }).text("Administer")
        );

        var readerCallback = $$menu.clickCallback;
        $$menu.click(function(e) {
            if (e.$item.is(".menu-administer")) {
                location.href = "/admin/test-access";
            } else if (readerCallback) {
                readerCallback(e);
            }
        });
    }
});
