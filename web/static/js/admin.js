/* ---- Invitations page: scroll-triggered pagination ---- */
$(function() {
    var $nextPage = $(".next-page");
    if (!$nextPage.length) {
        return;
    }

    var loading = false;

    function loadNextPage() {
        if (loading || !$nextPage.length) {
            return;
        }
        loading = true;
        $nextPage.text("Loading…");

        var status = $nextPage.data("status");
        var email  = $nextPage.data("email");
        var start  = $nextPage.data("start");

        var params = { partial: "1" };
        if (status) {
            params.status = status;
        }
        if (email) {
            params.email  = email;
        }
        if (start) {
            params.start  = start;
        }

        $.getJSON("/admin/invitations", params, function(data) {
            $("#invite-tbody").append(data.rows_html);
            if (data.next_start) {
                $nextPage.data("start", data.next_start).text("Load more");
            } else {
                $nextPage.remove();
                $nextPage = $();
            }
        }).fail(function() {
            $nextPage.text("Load more");
        }).always(function() {
            loading = false;
        });
    }

    var $content = $("#admin-content");
    $content.on("scroll", function() {
        if (!$nextPage.length) {
            return;
        }
        const contentBottom = $content.scrollTop() + $content.innerHeight();
        // offsetTop relative to the scrollable container
        var triggerTop = $nextPage[0].offsetTop;
        if (contentBottom >= triggerTop - 36) {
            loadNextPage();
        }
    });

    $nextPage.on("click", loadNextPage);
});

/* ---- Shared admin menu setup ---- */
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
