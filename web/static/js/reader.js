/*****************************************************************************
 ** Copyright (C) 2024-2025 Akop Karapetyan
 **
 ** Licensed under the Apache License, Version 2.0 (the "License");
 ** you may not use this file except in compliance with the License.
 ** You may obtain a copy of the License at
 **
 **     http://www.apache.org/licenses/LICENSE-2.0
 **
 ** Unless required by applicable law or agreed to in writing, software
 ** distributed under the License is distributed on an "AS IS" BASIS,
 ** WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 ** See the License for the specific language governing permissions and
 ** limitations under the License.
 ******************************************************************************
 */

 $().ready(function() {
    var $dragSource = null;
    var $dragClone = null;
    var dragDestination = null;

    var subscriptionMap = null;
    var continueFrom = null;
    var lastContinued = null;
    var lastGPressTime = 0;
    var lastRefresh = -1;
    var timeoutId = -1;

    const cookies = Cookies.withAttributes({ expires: 31 });

    // A 15x15 transparent image
    var transparentIcon = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAYAAAA71pVKAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsSAAALEgHS3X78AAAAB3RJTUUH3QkaEBchBQxHYwAAAbxJREFUKM+lkr1rFEEYxn8zs7eXu1u4i3prwJOAqBeicCBYCYIgCgraSBRt/ANSia2FdsbCIkVsLDVaqdiJYJqQWGkTUEyQBYNfJ5ecObMfszMWl2wIuYiQt5qB+T3P+77zwA5KACw9uYyTqv+GtEqpXHmKBDJQeP663j9r/b2TtVDop3jhPjYJMa0A0/qMDmYxzU/bi2Rwrkj64yOyfxDl11F+nVz9LHp+ivj9JDbubA+b9iLh6zuAQHo+cu8wbuMSzsFTqNoxwle3MSvfN8Fy4+TQd/oW7vHryIFhdDDN6sub6IU3iL4y+ROjIFVvZ1neh/KHUP4QAO6Ri0QzE0RvHyJKVdTAUdzGCPG7ya3OphXw59ko4dQ9dDCLKFXJn7yBKO4imnmATUJyh8+AUD3aXvt122kSTY+TzL1AuB5uYwS72sL8/ADKRVZqPWDHpXBujML5u8hyjXjuOViDrB4CIP210AV2H9g6M2mKDZcAsEkHdIxZ/oKs7EfkPUxzvgtXBjfHc+XR1bWbAqVAx9kSbdjGRr9B5ZClPZj2N8DiXXvcddYq7UbOpqDTTNksL27sI00w7a9ZtndcfwE4Q5nI69qxywAAAABJRU5ErkJggg==";

    var linkify = function(str, args) {
        const re = /\(((?:[a-z]+:\/\/|%(?:[0-9]+\$)?s)[^\)]*)\)\[([^\]]*)\]/g;
        var m;
        var start = 0;
        var html = "";
        var outArgs = [];

        while ((m = re.exec(str)) !== null) {
            const url = m[1];
            const text = m[2];
            const anchor = `<a href="${url}" target="_blank">${text}</a>`;

            html += str.substr(start, m.index - start) + anchor;
            start = m.index + m[0].length;

            outArgs.push(text);
        }

        html += str.substr(start);

        return { html: html, args: args ? args : outArgs };
    };

    var _l = function(str, args) {
        var localized = null;
        if (typeof gofrStrings !== "undefined" && gofrStrings != null)
            localized = gofrStrings[str];

        if (localized == null)
            localized = str; // No localization

        var md = linkify(localized, args);
        localized = md.html;
        if (md.args.length)
            args = md.args;

        if (args)
            return vsprintf(localized, args);

        return localized;
    };

    var getPublishedDate = function(dateAsString) {
        if (dateAsString === undefined) {
            return "";
        }
        var now = new Date();
        var date = new Date(dateAsString);

        var sameDay = now.getDate() == date.getDate()
            && now.getMonth() == date.getMonth()
            && now.getFullYear() == date.getFullYear();

        return dateTimeFormatter(date, sameDay);
    };

    // Automatic pager

    $(".gofr-entries-container").scroll(function() {
        var pagerHeight = $(".next-page").outerHeight();
        if (!pagerHeight)
            return; // No pager

        if (lastContinued == continueFrom)
            return;

        var offset = $("#gofr-entries").height() - ($(".gofr-entries-container").scrollTop() + $(".gofr-entries-container").height()) - pagerHeight;
        if (offset < 36)
            $(".next-page").click();
    });

    // Default click handler

    $("html")
        .click(function() {
            ui.unfloatAll();
        })
        .mouseup(function(e) {
            $("#subscriptions").unbind("mousemove");
            $("#subscriptions .dragging").remove();
            $("#subscriptions .dragged").removeClass("dragged");

            if ($dragSource && dragDestination) {
                var dragSource = $dragSource.data("subscription");
                if (dragDestination.id != (dragSource.parent || ""))
                    dragSource.moveTo(dragDestination);
            }

            $dragSource = null;
            $dragClone = null;
            dragDestination = null;
        });

    $(".modal-blocker").click(function() {
        $(".modal").showModal(false);
    });

    // Default error handler

    $(document).ajaxError(function(event, jqxhr, settings, exception) {
        var errorMessage;

        try {
            var errorJson = $.parseJSON(jqxhr.responseText)
            errorMessage = errorJson.errorMessage;
        } catch (exception) {
            errorMessage = _l("An unexpected error has occurred. Please try again later.");
        }

        if (errorMessage != null)
            ui.showToast(errorMessage, true);
        else if (errorJson.infoMessage != null)
            ui.showToast(errorJson.infoMessage, false);
    });

    var articleGroupingMethods = {
        "getFilter": function() {
            return { };
        },
        "getSourceUrl": function() {
            // returns source URL (e.g. http://www.arstechnica.com/)
            // or null if N/A
            return null;
        },
        "supportsAggregateActions": function() {
            return false;
        },
        "supportsPropertyFilters": function() {
            return false;
        },
        "getDom": function() {
            return $("#subscriptions").find(`.${this.domId}`);
        },
        "loadEntries": function() {
            lastContinued = continueFrom;

            const subscription = this;
            const filter = subscription.getFilter();
            if (filter.prop === undefined) {
                cookies.remove('filter');
            } else {
                cookies.set('filter', filter.prop);
            }
            if (continueFrom) {
                $.extend(filter, { "start": continueFrom });
            }

            $.ajax({
                url: "articles" + (filter ? `?${$.param(filter)}` : ""),
                dataType: "json",
                success: function(response) {
                    continueFrom = response.continue;
                    subscription.addPage(response.articles, response.continue);
                }
            });
        },
        "refresh": function() {
            continueFrom = null;
            lastContinued = null;

            $("#gofr-entries").empty();
            this.loadEntries();
        },
        "select": function(reloadItems /* = true */) {
            if (typeof reloadItems === "undefined")
                reloadItems = true;

            $("#subscriptions").find(".subscription.selected").removeClass("selected");
            this.getDom().addClass("selected");

            if (reloadItems) {
                this.selectedEntry = null;

                var sourceUrl = this.getSourceUrl();
                $("#gofr-entries").toggleClass("single-source",
                    sourceUrl != null);

                if (sourceUrl == null)
                    $(".gofr-entries-header").text(this.title);
                else
                    $(".gofr-entries-header").html($("<a />", {
                        "href" : sourceUrl,
                        "target" : "_blank"
                    }).text(this.title).append($("<span />").text(" »")));

                this.refresh();
                syncFeeds();
            }

            ui.onScopeChanged();
        },
        "addPage": function(entries) {
            var subscription = this;
            var idCounter = $("#gofr-entries").find(".gofr-entry").length;

            $.each(entries, function() {
                var entry = this;

                // Inject methods
                for (var name in entryMethods)
                    entry[name] = entryMethods[name];

                var entrySubscription = entry.getSubscription();
                if (!entrySubscription)
                    return true; // May have been deleted on server; don't add it if so

                var sourceTitle = entrySubscription != null ? entrySubscription.title : null;

                entry.areExtrasDirty = true;
                entry.extras = { "likeCount": 0 };
                entry.domId = `gofr-entry-${idCounter++}`;

                var $entry = $("<div />", { "class": `gofr-entry ${entry.domId}` })
                    .data("entry", entry)
                    .append($("<div />", { "class" : "gofr-entry-item" })
                        .append($("<div />", { "class" : "action-star" })
                            .click(function(e) {
                                entry.toggleStarred();
                                e.stopPropagation();
                            }))
                        .append($("<span />", { "class" : "gofr-entry-source" })
                            .text(sourceTitle))
                        .append($("<a />", { "class" : "gofr-entry-link", "href" : entry.link, "target" : "_blank" })
                            .click(function(e) {
                                // Prevent expansion
                                e.stopPropagation();
                            }))
                        .append($("<span />", { "class" : "gofr-entry-pubDate" })
                            .text(getPublishedDate(entry.published)))
                        .append($("<div />", { "class" : "gofr-entry-excerpt" })
                            .append($("<h2 />", { "class" : "gofr-entry-title" })
                            // .append($("<a />", { "class" : "gofr-entry-title", "href" : entry.link, "target" : "_blank" })
                                // .click(function(e) {
                                // 	entry.markAsRead();

                                // 	// Prevent expansion
                                // 	e.stopPropagation();
                                // })
                                .text(entry.title))
                            .append($("<span />", { "class" : "gofr-entry-source-mobile" })
                                .text(` - ${sourceTitle}`))
                            ))
                    .click(function() {
                        entry.select();

                        var wasExpanded = entry.isExpanded();

                        ui.collapseAllEntries();
                        if (!wasExpanded) {
                            entry.expand();
                            entry.scrollIntoView();
                        }
                    });

                if (entry.summary) {
                    $entry.find(".gofr-entry-excerpt")
                        .append($("<span />", { "class" : "gofr-entry-spacer" }).text(" - "))
                        .append($("<span />", { "class" : "gofr-entry-summary" }).text(entry.summary));
                }

                $("#gofr-entries").append($entry);

                entry.syncView();
            });

            $(".next-page").remove();

            ui.onEntryListUpdate();

            if (continueFrom) {
                $("#gofr-entries")
                    .append($("<div />", { "class" : "next-page" })
                        .text(_l("Continue"))
                        .click(function(e) {
                            subscription.loadEntries();
                        }));
            }
        },
    };

    var subscriptionMethods = $.extend({}, articleGroupingMethods, {
        "getFilter": function() {
            const selectedPropertyFilter = $(".group-filter.selected-menu-item").data("value");

            const filter = { "sub": this.id };
            if (selectedPropertyFilter) {
                $.extend(filter, { "prop": selectedPropertyFilter });
            }
            return filter;
        },
        "supportsAggregateActions": function() {
            return true;
        },
        "supportsPropertyFilters": function() {
            return true;
        },
        "getDom": function() {
            return $("#subscriptions").find(`.${this.domId}`);
        },
        "isFolder": function() {
            return false;
        },
        "isRoot": function() {
            return false;
        },
        "getSourceUrl": function() {
            return this.link;
        },
        "getFavIconUrl": function() {
            return this.favIconUrl;
        },
        "getChildren": function() {
            var subscription = this;
            var children = [];

            $.each(subscriptionMap, function(key, sub) {
                if (subscription.id === "" || sub.parent === subscription.id)
                    children.push(sub);
            });

            return children;
        },
        "syncView": function($sub) {
            var $sub = this.getDom();
            var $item = $sub.find("> .subscription-item");
            var $title = $item.find(".subscription-title");
            var $unreadCount = $item.find(".subscription-unread-count");

            $title.text(this.title);
            $unreadCount.text(_l("(%d)", [this.unread]));
            $item
                .toggleClass("has-unread", this.unread > 0)
                .attr("title", this.title);
            $sub.toggleClass("no-unread", this.unread < 1);

            var parent = this.getParent();
            if (parent)
                parent.syncView();

            var len = $title.outerWidth() + $unreadCount.outerWidth() + 14;
            var available = $item.width() - $title.offset().left;

            $item.toggleClass("too-long", len >= available);

            if (!this.isRoot())
                this.getRoot().syncView();
        },
        "getType": function() {
            return "leaf";
        },
        "getParent": function() {
            if (!this.parent)
                return null;

            return subscriptionMap[this.parent];
        },
        "getRoot": function() {
            return subscriptionMap[""];
        },
        "updateUnreadCount": function(byHowMuch) {
            this.unread += byHowMuch;

            var parent = this.getParent();
            if (parent != null)
                parent.unread += byHowMuch;

            this.getRoot().unread += byHowMuch;
        },
        "rename": function(newName) {
            const sub = this;
            $.ajax({
                url: "rename",
                type: "POST",
                data: JSON.stringify({
                    "id": sub.id,
                    "title": newName,
                }),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function(response) {
                    resetSubscriptionDom(response.subscriptions, false);
                }
            });
        },
        "unsubscribe": function() {
            var sub = this;
            if (!sub.isFolder()) {
                $.ajax({
                    url: "unsubscribe",
                    type: "POST",
                    data: JSON.stringify({
                        "id": sub.id,
                    }),
                    contentType: "application/json; charset=utf-8",
                    dataType: "json",
                    success: function(response) {
                        resetSubscriptionDom(response.subscriptions, false);
                        ui.pruneDeadEntries();
                    }
                });
            }
        },
        "markAllAsRead": function() {
            const sub = this;
            $.ajax({
                url: "markAllAsRead",
                type: "POST",
                data: JSON.stringify({
                    "scope": sub.isRoot()
                        ? "all"
                        : (sub.isFolder()
                            ? "folder"
                            : "subscription"
                        ),
                    "id": sub.id ? sub.id : undefined,
                }),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function(response) {
                    resetSubscriptionDom(response.subscriptions, false);
                    // build sub id to unread count map
                    const map = response.subscriptions.subscriptions.reduce(function(acc, sub) {
                        acc[sub.id] = sub.unread;
                        return acc;
                    }, {});
                    // for any entries with belonging to subs with unread count
                    // zero, mark them as read
                    $("#gofr-entries .gofr-entry").each(function() {
                        const entry = $(this).data("entry");
                        if (map[entry.source] == 0 && entry.hasProperty("unread")) {
                            entry.properties = entry.properties.filter(p => p != "unread");
                            entry.syncView();
                        }
                    });
                }
            });
        },
        "moveTo": function(folder) {
            var sub = this;
            $.ajax({
                url: "moveSub",
                type: "POST",
                data: JSON.stringify({
                    "id": sub.id,
                    "destination":  folder.id ? folder.id : undefined,
                }),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function(response) {
                    resetSubscriptionDom(response.subscriptions, false);
                }
            });
        },
    });

    var folderMethods = $.extend({}, subscriptionMethods, {
        "getFilter": function() {
            var selectedPropertyFilter = $(".group-filter.selected-menu-item").data("value");

            const filter = {};
            if (this.id) {
                $.extend(filter, { "folder": this.id });
            }
            if (selectedPropertyFilter) {
                $.extend(filter, { "prop": selectedPropertyFilter });
            }
            return filter;
        },
        "getSourceUrl": function() {
            return null;
        },
        "subscribe": function(url) {
            const folderId = this.id;
            $.ajax({
                url: "subscribe",
                type: "POST",
                data: JSON.stringify({
                    "url": url,
                    "folderId": folderId ? folderId : undefined,
                }),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function(response) {
                    // Meh
                    // resetSubscriptionDom(response.subscriptions, false);
                }
            });
        },
        "isFolder": function() {
            return true;
        },
        "isRoot": function() {
            return this.id == "";
        },
        "getType": function() {
            if (this.isRoot())
                return "root";

            return "folder";
        },
        "remove": function() {
            var folder = this;
            $.ajax({
                url: "deleteFolder",
                type: "POST",
                data: JSON.stringify({
                    "id": folder.id,
                }),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function(response) {
                    resetSubscriptionDom(response.subscriptions, false);
                    ui.pruneDeadEntries();
                }
            });
        },
    });

    var tagMethods = $.extend({}, articleGroupingMethods, {
        "getFilter": function() {
            return { "tag": this.title, };
        },
        "getSourceUrl": function() {
            return null;
        },
        "supportsAggregateActions": function() {
            return false;
        },
        "supportsPropertyFilters": function() {
            return false;
        },
        "remove": function() {
            var tag = this;
            $.ajax({
                url: "removeTag",
                type: "POST",
                data: JSON.stringify({
                    "tag": tag.title,
                }),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function(response) {
                    // FIXME: remove all matching tags from existing entries
                    resetSubscriptionDom(response.subscriptions, false);
                }
            });
        },
    });

    var specialFolderMethods = $.extend({}, articleGroupingMethods, {
        "getFilter": function() {
            return this.filter;
        },
        "getSourceUrl": function() {
            return null;
        },
        "supportsAggregateActions": function() {
            return false;
        },
        "supportsPropertyFilters": function() {
            return false;
        },
    });

    var entryMethods = {
        "getSubscription": function() {
            return subscriptionMap[this.source];
        },
        "getDom": function() {
            return $("#gofr-entries").find(`.${this.domId}`);
        },
        "hasProperty": function(propertyName) {
            return $.inArray(propertyName, this.properties) > -1;
        },
        "markAsRead": function(force) {
            if (this.hasProperty("unread") || force) {
                this.setProperty("unread", false);
            }
        },
        "setProperty": function(propertyName, propertyValue) {
            if (propertyValue == this.hasProperty(propertyName))
                return; // Already set

            var entry = this;

            $.ajax({
                url: "setProperty",
                type: "POST",
                data: JSON.stringify({
                    "article": this.id,
                    "property": propertyName,
                    "set": propertyValue,
                }),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function(properties) {
                    delete entry.properties;
                    entry.properties = properties;

                    if (propertyName == "unread") {
                        var subscription = entry.getSubscription();
                        subscription.updateUnreadCount(propertyValue ? 1 : -1);

                        subscription.syncView();
                        ui.updateUnreadCount();
                    } else if (propertyName == "like") {
                        var delta = propertyValue ? 1 : -1;
                        entry.extras.likeCount += delta;
                    }

                    entry.syncView();
                }
            });
        },
        "toggleStarred": function(propertyName) {
            this.toggleProperty("star");
        },
        "toggleUnread": function() {
            this.toggleProperty("unread");
        },
        "toggleLike": function() {
            this.toggleProperty("like");
        },
        "toggleProperty": function(propertyName) {
            this.setProperty(propertyName,
                !this.hasProperty(propertyName));
        },
        "syncView": function() {
            var $entry = this.getDom();
            $entry
                .toggleClass("star", this.hasProperty("star"))
                .toggleClass("like", this.hasProperty("like"))
                .toggleClass("read", !this.hasProperty("unread"));
            $entry.find(".gofr-like-count")
                .text(_l("(%d)", [this.extras.likeCount]))
                .toggleClass("unliked", this.extras.likeCount < 1);

            var $tagNode = $entry.find(".action-tag");
            $tagNode.toggleClass("has-tags", this.tags.length > 0);
            $tagNode.find(".gofr-action-text")
                .text(this.tags.length > 0
                    ? _l("%1$s", [ this.tags.join(", ") ])
                    : _l("Tag"));
        },
        "isExpanded": function() {
            return this.getDom().hasClass("open");
        },
        "resolveUrl": function(url) {
            if (!url || url.match(/^\s*(?:[a-z]+:)?\/\//))
                return url; // Invalid or already absolute

            if (typeof this.articleRoot === "undefined")
            {
                // Determine and store article root and path
                var articleUrl = this.link;

                this.articleRoot = articleUrl;
                this.articlePath = articleUrl;

                var m = articleUrl.match(/^([^:]+:\/\/[^/]+)\//);
                if (m)
                    this.articleRoot = m[1];

                m = articleUrl.match(/(\/[^\/]*)$/);
                if (m && m.index >= this.articleRoot.length)
                    this.articlePath = articleUrl.substr(0, m.index);
            }

            if (url) {
                if (url.substr(0, 1) == "/")
                    url = this.articleRoot + url;
                else
                    url = `${this.articlePath}/${url}`;
            }

            return url;
        },
        "expand": function() {
            var entry = this;
            var subscription = this.getSubscription();
            var $entry = this.getDom();

            if (this.isExpanded())
                return;

            this.markAsRead();

            // FIXME
            // if (entry.areExtrasDirty)
            //     entry.loadExtras();

            var $content =
                $("<div />", { "class" : "gofr-entry-content" })
                    .append($("<div />", { "class": "gofr-article" })
                        .append($("<a />", { "href": entry.link, "target": "_blank", "class": "gofr-article-title" })
                            .append($("<h2 />")
                                .text(entry.title)))
                        .append($("<div />", { "class": "gofr-article-author" }))
                        .append($("<div />", { "class": "gofr-article-pubDate" })
                            .text(_l("Published %1$s", [getPublishedDate(entry.published)])))
                        .append($("<div />", { "class": "gofr-media-container" }))
                        .append($("<div />", { "class": "gofr-article-body" })
                            .append(entry.content)))
                    .append($("<div />", { "class": "gofr-entry-footer"})
                        .append($("<span />", { "class": "action-star" })
                            .click(function(e) {
                                entry.toggleStarred();
                            }))
                        .append(
                            $("<span />", { "class" : "action-unread gofr-entry-action"})
                                .append(
                                    $("<span />", { "class": "gofr-action-icon" })
                                        .text("📩")
                                )
                                .append(
                                    $("<span />", { "class": "gofr-action-text" })
                                        .text(_l("Keep unread"))
                                )
                                .click(function(e) {
                                    entry.toggleUnread();
                                    entry.syncView();
                                })
                        )
                        .append(
                            $("<span />", { "class" : "action-tag gofr-entry-action" })
                                .append(
                                    $("<span />", { "class": "gofr-action-icon" })
                                        .text("🏷️")
                                )
                                .append(
                                    $("<span />", { "class": "gofr-action-text" })
                                        .text(
                                            this.tags.length
                                                ? _l("%1$s", [ this.tags.join(", ") ])
                                                : _l("Tag")
                                        )
                                )
                                .click(function(e) {
                                    ui.editTags(entry);
                                })
                        )
                        .append(
                            $("<span />", { "class" : "action-like gofr-entry-action"})
                                .append(
                                    $("<span />", { "class": "gofr-action-icon" })
                                        .text("👍")
                                )
                                .append(
                                    $("<span />", { "class": "gofr-action-text" })
                                        .text(_l("Like"))
                                )
                                .append(
                                    $("<span />", { "class": "gofr-like-count" })
                                        .text(_l("(%d)", [entry.extras.likeCount]))
                                        .toggleClass("unliked", this.extras.likeCount < 1)
                                )
                                .click(function(e) {
                                    entry.toggleLike();
                                })
                        )
                        // .append($("<span />", { "class" : "gofr-entry-action-group gofr-entry-share-group"})
                        //     .append($("<span />", { "class": "gofr-action-text" })
                        //         .text(_l("Share: "))))
                        // .append($("<a />", {
                        //     "class": "action-share-gplus gofr-entry-share",
                        //     "href": `https://plus.google.com/share?url=${encodeURIComponent(entry.link)}`,
                        //     "data-flags": "width=600,height=460,menubar=no,location=no,status=no",
                        //     "title": _l("Share on Google+"),
                        // })
                        // .html("&nbsp;")
                        // .click(function(e) {
                        //     return ui.share($(this));
                        // }))
                        // .append($("<a />", {
                        //     "class": "action-share-fb gofr-entry-share",
                        //     "href": `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(entry.link)}`,
                        //     "data-flags": "width=626,height=436,menubar=no,location=no,status=no",
                        //     "title": _l("Share on Facebook"),
                        // })
                        // .html("&nbsp;")
                        // .click(function(e) {
                        //     return ui.share($(this));
                        // }))
                        // .append($("<a />", {
                        //     "class": "action-share-twitter gofr-entry-share",
                        //     "href": `https://twitter.com/share?url=${encodeURIComponent(entry.link)}`,
                        //     "data-flags": "width=470,height=257,menubar=no,location=no,status=no",
                        //     "title": _l("Tweet"),
                        // })
                        // .html("&nbsp;")
                        // .click(function(e) {
                        //     return ui.share($(this));
                        // }))
                    )
                    .click(function(e) {
                        ui.unfloatAll();
                        e.stopPropagation();
                    });

            var template;
            if (entry.author)
                template = _l("From (%1$s)[%2$s] by %3$s", [subscription.link, subscription.title, entry.author]);
            else
                template = _l("From (%1$s)[%2$s]", [subscription.link, subscription.title]);

            $content.find(".gofr-article-author").html(template);
            if (!subscription.link)
                $content.find(".gofr-article-author a").contents().unwrap();

            // Whether tags are set
            $content.find(".action-tag").toggleClass("has-tags", this.tags.length > 0);

            // Links in the content should open in a new window
            $content.find(".gofr-article-body a").attr("target", "_blank");

            // Resolve relative URLs
            $content.find(".gofr-article-body img").not("[src^='http'],[src^='https']").each(function() {
                $(this).attr("src", function(index, value) {
                    return entry.resolveUrl(value);
                })
            });
            $content.find(".gofr-article-body a").not("[href^='http'],[href^='https']").each(function() {
                $(this).attr("href", function(index, value) {
                    if (!value)
                        return value;

                    return entry.resolveUrl(value);
                })
            });

            // Add any media
            if (entry.media) {
                var $mediaContainer = $content.find(".gofr-media-container");
                $.each(entry.media, function() {
                    var media = this;
                    var $audio = $("<audio />", { "controls": "controls" })
                        .append($("<source />", { "src": media.url, "type": media.type }))
                        .append($("<embed />", { "class": "gofr-embedded-media", "src": media.url }));

                    $mediaContainer.append($audio);
                });
            }

            $entry.toggleClass("open", true);
            $entry.append($content);
        },
        "scrollIntoView": function() {
            this.getDom()[0].scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        },
        "collapse": function() {
            this.getDom()
                .removeClass("open")
                .find(".gofr-entry-content")
                    .remove();
        },
        "select": function() {
            $("#gofr-entries").find(".gofr-entry.selected").removeClass("selected");
            this.getDom().addClass("selected");
        },
        "loadExtras": function() {
            var entry = this;
            // FIXME: this call is missing
            $.ajax({
                url: "articleExtras",
                data: {
                    "article": this.id,
                    "subscription": this.source,
                    "folder": this.getSubscription().parent,
                },
                dataType: "json",
                success: function(response) {
                    entry.extras = response;
                    entry.areExtrasDirty = false;
                    entry.syncView();
                }
            });
        },
    };

    $$menu.click(function(e) {
        var $item = e.$item;
        if ($item.is(".menu-all-items, .menu-new-items")) {
            var subscription = getSelectedSubscription();
            if (subscription != null)
                subscription.refresh();
            ui.onScopeChanged();
        } else if ($item.is(".menu-show-sidebar")) {
            ui.toggleSidebar(e.isChecked);
        } else if ($item.is(".menu-import-subscriptions")) {
            ui.showImportSubscriptionsModal();
        } else if ($item.is(".menu-export-subscriptions")) {
            ui.exportSubscriptions();
        } else if ($item.is(".menu-show-all-subs")) {
            ui.toggleReadSubscriptions(e.isChecked);
        } else if ($item.is(".menu-create-folder")) {
            ui.createFolder();
        } else if ($item.is(".menu-sign-out")) {
            $("#sign-out")[0].click();
        } else if ($item.is(".menu-shortcuts")) {
            $(".shortcuts").show();
        } else if ($item.is(".menu-subscribe, .menu-rename, .menu-unsubscribe, .menu-delete-folder")) {
            var subscription = subscriptionMap[e.context];
            if ($item.is(".menu-subscribe")) {
                ui.subscribe(subscription);
            } else if ($item.is(".menu-rename")) {
                ui.rename(subscription);
            } else if ($item.is(".menu-unsubscribe")) {
                ui.unsubscribe(subscription);
            } else if ($item.is(".menu-delete-folder")) {
                ui.removeFolder(subscription);
            }
        } else if ($item.is(".menu-delete-tag")) {
            var tag = $(`.${e.context}`).data("subscription");
            ui.deleteTag(tag);
        }
    });

    var ui = {
        "init": function() {
            this.localizeStatics();
            this.initHelp();
            this.initButtons();
            this.initMenus();
            this.initShortcuts();
            this.initModals();
            this.initFileInputs();
            this.initBookmarklet();

            const showSidebar = cookies.get("show-sidebar") !== "false";
            const showAllSubs = cookies.get("show-all-subs") !== "false";
            const filter = cookies.get("filter");

            const cookieNames = [ "filter", "show-sidebar", "show-all-subs" ];
            $.each(cookieNames, function(_, name) {
                const value = cookies.get(name);
                if (value) {
                    cookies.set(name, value);
                }
            });

            if (filter == 'unread') {
                $('#menu-filter').selectItem('.menu-new-items');
                $('#menu-view').selectItem('.menu-new-items');
            } else {
                $('#menu-filter').selectItem('.menu-all-items');
                $('#menu-view').selectItem('.menu-all-items');
            }
            this.onScopeChanged();

            this.toggleSidebar(showSidebar);
            this.toggleReadSubscriptions(showAllSubs);

            $("a").not("#sign-out").attr("target", "_blank");
            $("#sign-out")
                .click(function(_) {
                    $.each(cookieNames, function(_, name) {
                        cookies.remove(name);
                    });
                });
        },
        "isNavBarVisible": function() {
            return $("body").is(".sidebar-open");
        },
        "toggleNavBar": function(show) {
            if (typeof show === "undefined")
                show = !ui.isNavBarVisible();

            $("body").toggleClass("sidebar-open", show);
        },
        "initButtons": function() {
            $("button.refresh").click(function() {
                refresh();
            });
            $("button.subscribe").click(function() {
                ui.subscribe();
            });
            $("button.navigate").click(function(e) {
                $$menu.hideAll();
                ui.toggleNavBar(true);
                e.stopPropagation();
            });
            $(".select-article.up").click(function() {
                ui.openArticle(-1);
            });
            $(".select-article.down").click(function() {
                ui.openArticle(1);
            });
            $(".mark-all-as-read").click(function() {
                ui.markAllAsRead();
            });

            $("#import-subscriptions .modal-ok").click(function() {
                var $modal = $(this).closest(".modal");
                var $form = $("#import-subscriptions form");

                if (!$form.find("input[type=file]").val()) {
                    // No file specified
                    return;
                }

                $.ajax({
                    url: "importFeeds",
                    type: "POST",
                    cache: false,
                    contentType: false,
                    processData: false,
                    data: new FormData($form[0]),
                    success: function(){
                        // resetSubscriptionDom(response.subscriptions, false);
                        $modal.showModal(false);
                        // ui.showToast(response.message, false);
                    }
                });
            });
        },
        "initMenus": function() {
            $("body")
                .append($("<ul />", { "id": "menu-filter", "class": "menu selectable" })
                    .append($("<li />", { "class": "menu-all-items group-filter" }).text(_l("All items")))
                    .append($("<li />", { "class": "menu-new-items group-filter", "data-value": "unread" }).text(_l("New items"))))
                .append($("<ul />", { "id": "menu-settings", "class": "menu" })
                    .append($("<li />", { "class": "menu-show-sidebar checkable" }).text(_l("Show sidebar")))
                    .append($("<li />", { "class": "menu-show-all-subs checkable" }).text(_l("Show read subscriptions")))
                    .append($("<li />", { "class": "divider" }))
                    .append($("<li />", { "class": "menu-shortcuts" }).text(_l("View shortcut keys…"))))
                .append($("<ul />", { "id": "menu-view", "class": "menu selectable" })
                    .append($("<li />", { "class": "menu-all-items group-filter" }).text(_l("All items")))
                    .append($("<li />", { "class": "menu-new-items group-filter", "data-value": "unread" }).text(_l("New items"))))
                .append($("<ul />", { "id": "menu-user-options", "class": "menu" })
                    .append($("<li />", { "class": "menu-import-subscriptions" }).text(_l("Import subscriptions…")))
                    .append($("<li />", { "class": "menu-export-subscriptions" }).text(_l("Export subscriptions")))
                    .append($("<li />", { "class": "divider" }))
                    .append($("<li />", { "class": "menu-sign-out" }).text(_l("Sign out"))))
                .append($("<ul />", { "id": "menu-folder", "class": "menu" })
                    .append($("<li />", { "class": "menu-subscribe" }).text(_l("Subscribe…")))
                    .append($("<li />", { "class": "menu-rename" }).text(_l("Rename…")))
                    .append($("<li />", { "class": "menu-delete-folder" }).text(_l("Delete…"))))
                .append($("<ul />", { "id": "menu-tag", "class": "menu" })
                    .append($("<li />", { "class": "menu-delete-tag" }).text(_l("Remove tag…"))))
                .append($("<ul />", { "id": "menu-root", "class": "menu" })
                    .append($("<li />", { "class": "menu-create-folder" }).text(_l("New folder…")))
                    .append($("<li />", { "class": "menu-subscribe" }).text(_l("Subscribe…"))))
                .append($("<ul />", { "id": "menu-leaf", "class": "menu" })
                    .append($("<li />", { "class": "menu-rename" }).text(_l("Rename…")))
                    .append($("<li />", { "class": "menu-unsubscribe" }).text(_l("Unsubscribe…"))));

            $(".menu li").not(".divider").wrapInner("<span />");
        },
        "initHelp": function() {
            var categories = [{
                "title": _l("Navigation"),
                "shortcuts": [
                    { keys: _l("[J]/[K]"),       action: _l("Open next/previous article") },
                    { keys: _l("[N]/[P]"),       action: _l("Move to next/previous article") },
                    { keys: _l("[Shift]+[N]/[P]"), action: _l("Move to next/previous subscription") },
                    { keys: _l("[Shift]+[O]"),   action: _l("Open subscription or folder") },
                    { keys: _l("[G] then [A]"), action: _l("Open All Items") },
                ]}, {
                "title": _l("Application"),
                "shortcuts": [
                    { keys: _l("[R]"), action: _l("Refresh") },
                    { keys: _l("[U]"), action: _l("Toggle sidebar") },
                    { keys: _l("[A]"), action: _l("Add subscription") },
                    { keys: _l("[?]"), action: _l("Help") },
                ]}, {
                "title": _l("Articles"),
                "shortcuts": [
                    { keys: _l("[M]"),       action: _l("Mark as read/unread") },
                    { keys: _l("[S]"),       action: _l("Star article") },
                    { keys: _l("[V]"),       action: _l("Open link") },
                    { keys: _l("[O]"),       action: _l("Open article") },
                    { keys: _l("[T]"),       action: _l("Tag article") },
                    { keys: _l("[L]"),         action: _l("Like article") },
                    { keys: _l("[Shift]+[A]"), action: _l("Mark all as read") },
                ]}];

            var maxColumns = 2; // Number of columns in the resulting table

            // Build the table
            var $table = $("<table/>");
            for (var i = 0, n = categories.length; i < n; i += maxColumns) {
                var keepGoing = true;
                for (var k = -1; keepGoing; k++) {
                    var $row = $("<tr/>");
                    $table.append($row);
                    keepGoing = false;

                    for (var j = 0; j < maxColumns && i + j < n; j++) {
                        var category = categories[i + j];

                        if (k < 0) { // Header
                            $row.append($("<th/>", { "colspan": 2 })
                                .text(category.title));
                            keepGoing = true;
                        } else if (k < category.shortcuts.length) {
                            var words = category.shortcuts[k].keys.split(/\[|\]/) ;
                            var $div = $("<div />");

                            for (var w = 0; w < words.length; w++) {
                                if (w % 2)
                                    $div.append($("<span />", { "class": "key" }).text(words[w]));
                                else
                                    $div.append(words[w]);
                            }

                            $row.append($("<td/>", { "class": "sh-keys" })
                                .append($div))
                            .append($("<td/>", { "class": "sh-action" })
                                .text(category.shortcuts[k].action));
                            keepGoing = true;
                        } else { // Empty cell
                            $row.append($("<td/>", { "colspan": 2 }));
                        }
                    }
                }
            }

            $(".about").click(function() {
                ui.showAbout();
                return false;
            });

            $("body").append($("<div />", { "class": "shortcuts" }).append($table));
        },
        "initBookmarklet": function() {
            var subscribeUrl = `${location.protocol}//${location.host}/subBm?url=`;
            var bookmarklet = "javascript:(function(){open(\"" + subscribeUrl + "\" + encodeURIComponent(location.href));})()";

            $(".bookmarklet")
                .attr("href", bookmarklet)
                .click(function() {
                    window.alert(_l("1. Drop this shortcut in your Bookmarks bar\n2. While browsing the web, click the bookmark to subscribe"));

                    return false;
                });
        },
        "initShortcuts": function() {
            $(document)
                .bind("keypress", "", function(e) {
                    var isNavBarKey = e.charCode >= 78 && e.charCode <= 80;
                    if (!ui.isNavBarVisible() || !isNavBarKey)
                        ui.toggleNavBar(false);

                    $(".shortcuts").hide();
                    $$menu.hideAll();
                })
                .bind("keypress", "n", function() {
                    ui.selectArticle(1);
                })
                .bind("keypress", "p", function() {
                    ui.selectArticle(-1);
                })
                .bind("keypress", "j", function() {
                    ui.openArticle(1);
                })
                .bind("keypress", "k", function() {
                    ui.openArticle(-1);
                })
                .bind("keypress", "o", function() {
                    ui.openArticle(0);
                })
                .bind("keypress", "r", function() {
                    refresh();
                })
                .bind("keypress", "s", function() {
                    if ($(".gofr-entry.selected").length)
                        $(".gofr-entry.selected").data("entry").toggleStarred();
                })
                .bind("keypress", "m", function() {
                    if ($(".gofr-entry.selected").length)
                        $(".gofr-entry.selected").data("entry").toggleUnread();
                })
                .bind("keypress", "l", function() {
                    if ($(".gofr-entry.selected").length)
                        $(".gofr-entry.selected").data("entry").toggleLike();
                })
                .bind("keypress", "shift+n", function() {
                    ui.highlightSubscription(1);
                })
                .bind("keypress", "shift+p", function() {
                    ui.highlightSubscription(-1);
                })
                .bind("keypress", "shift+o", function() {
                    if ($(".subscription.highlighted").length) {
                        $(".subscription.highlighted")
                            .removeClass("highlighted")
                            .data("subscription").select();
                    }
                })
                .bind("keypress", "g", function() {
                    lastGPressTime = new Date().getTime();
                })
                .bind("keypress", "a", function() {
                    if (ui.isGModifierActive())
                        $(".subscription.root")
                            .data("subscription").select();
                    else
                        ui.subscribe();
                })
                .bind("keypress", "u", function() {
                    ui.toggleSidebar();
                })
                .bind("keypress", "v", function() {
                    if ($(".gofr-entry.selected").length)
                        $(".gofr-entry.selected").find(".gofr-entry-link")[0].click();
                })
                .bind("keypress", "t", function() {
                    if ($(".gofr-entry.selected").length)
                        ui.editTags($(".gofr-entry.selected").data("entry"));
                })
                .bind("keypress", "shift+a", function() {
                    ui.markAllAsRead();
                })
                .bind("keypress", "shift+?", function() {
                    $(".shortcuts").show();
                });
        },
        "initModals": function() {
            $(".modal").wrapInner("<div class=\"modal-inner\"></div>").hide();

            $.fn.showModal = function(show) {
                if (!$(this).hasClass("modal")) {
                    return;
                }

                const $modal = $(this);
                $("body").toggleClass("modal-open", show);

                if (show) {
                    $modal.css("margin-top", -($modal.outerHeight() / 2) + "px");
                    $modal.show();
                } else {
                    $modal.hide();
                    $modal.find("form").each(function() {
                        this.reset();
                    });
                }
            };

            $(".modal-cancel").click(function() {
                $(this).closest(".modal").showModal(false);
                return false;
            });
        },
        "initFileInputs": function() {
            $("input[type=file]").each(function() {
                const $input = $(this);
                const $label = $input.next(".upload-proxy");
                const $path = $label.find(".upload-path")
                $input.closest("form").on("reset", function() {
                    $path.text(_l("No file selected"));
                    $path.toggleClass("selected", false);
                });
                $input.on("change", function(e) {
                    var path = _l("No file selected");
                    if (this.files && this.files.length > 1) {
                        path = ($input.attr("data-multiple-caption") || "").replace('{count}', this.files.length);
                    } else if (e.target.value) {
                        path = e.target.value.split('\\').pop();
                    }
                    $path.text(path);
                    $path.toggleClass("selected", path);
                });
            });
        },
        "showImportSubscriptionsModal": function() {
            $("#import-subscriptions").find("form")[0].reset();
            $("#import-subscriptions").showModal(true);
        },
        "exportSubscriptions": function() {
            window.location.href = "/exportOpml";
        },
        "showAbout": function() {
            $("#about").showModal(true);
        },
        "isGModifierActive": function() {
            return new Date().getTime() - lastGPressTime < 1000;
        },
        "toggleSidebar": function(showSidebar) {
            if (typeof showSidebar === "undefined")
                showSidebar = $(".navigate").is(":visible");

            $("body").toggleClass("floated-sidebar", !showSidebar);
            $(".menu-show-sidebar").setChecked(showSidebar);

            cookies.set("show-sidebar", showSidebar);
        },
        "toggleReadSubscriptions": function(showAllSubscriptions) {
            if (typeof showAllSubscriptions === "undefined")
                showAllSubscriptions = $("body").hasClass("hide-read-subs");

            $("body").toggleClass("hide-read-subs", !showAllSubscriptions);
            $(".menu-show-all-subs").setChecked(showAllSubscriptions);

            cookies.set("show-all-subs", showAllSubscriptions);
        },
        "updateUnreadCount": function() {
            // Update the "new items" caption in the dropdown to reflect
            // the unread count

            const selectedSubscription = getSelectedSubscription();
            var caption;

            if (!selectedSubscription || selectedSubscription.unread === null) {
                caption = _l("New items");
            } else if (selectedSubscription.unread == 0) {
                caption = _l("No new items");
            } else {
                caption = _l("%1$s new item(s)", [selectedSubscription.unread]);
            }

            $(".menu-new-items").setTitle(caption);

            // Update the title bar

            const selectionTitle = $(".subscription.selected")
                .find(".subscription-title")
                .first()
                .text();
            const unreadCount = subscriptionMap[""].unread;
            const unreadCountText = unreadCount > 0
                ? ` (${unreadCount})`
                : "";

            document.title = _l("%1$s — Grouch%2$s", [selectionTitle, unreadCountText]);
        },
        "highlightSubscription": function(which, scrollIntoView) {
            var $highlighted = $(".subscription.highlighted");
            if (!$highlighted.length)
                $highlighted = $(".subscription.selected");

            var $next = null;
            var $allFeeds = $("#subscriptions .subscription:visible");
            var highlightedIndex = $allFeeds.index($highlighted);

            if (which < 0) {
                if (highlightedIndex - 1 >= 0)
                    $next = $($allFeeds[highlightedIndex - 1]);
            } else if (which > 0) {
                if ($highlighted.length < 1)
                    $next = $($allFeeds[0]);
                else {
                    if (highlightedIndex + 1 < $allFeeds.length)
                        $next = $($allFeeds[highlightedIndex + 1]);
                }
            }

            if ($next) {
                $(".subscription.highlighted").removeClass("highlighted");
                $next.addClass("highlighted");

                scrollIntoView = (typeof scrollIntoView !== "undefined") ? scrollIntoView : true;
                if (scrollIntoView) {
                    $(".subscription.highlighted")[0].scrollIntoView({
                        behavior: "smooth",
                        block: "center",
                    });
                }
            }
        },
        "selectArticle": function(which, scrollIntoView) {
            if (which < 0) {
                if ($(".gofr-entry.selected").prev(".gofr-entry").length > 0)
                    $(".gofr-entry.selected")
                        .removeClass("selected")
                        .prev(".gofr-entry")
                        .addClass("selected");
            } else if (which > 0) {
                var $next = null;
                var $selected = $(".gofr-entry.selected");

                if ($selected.length < 1)
                    $next = $("#gofr-entries .gofr-entry:first");
                else
                    $next = $selected.next(".gofr-entry");

                $(".gofr-entry.selected").removeClass("selected");
                $next.addClass("selected");

                if ($next.next(".gofr-entry").length < 1)
                    $(".next-page").click(); // Load another page - this is the last item
            }

            scrollIntoView = (typeof scrollIntoView !== "undefined") ? scrollIntoView : true;
            if (scrollIntoView)
                $(".gofr-entry.selected")[0].scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                });
        },
        "openArticle": function(which) {
            this.selectArticle(which, false);

            if (!$(".gofr-entry-content", $(".gofr-entry.selected")).length || which === 0) {
                $(".gofr-entry.selected")
                    .click()
                    [0]
                    .scrollIntoView();
            }
        },
        "collapseAllEntries": function() {
            $(".gofr-entry.open").removeClass("open");
            $(".gofr-entry .gofr-entry-content").remove();
        },
        "showToast": function(message, isError) {
            if (message) {
                $("#toast span").text(message);
                $("#toast").attr("class", isError ? "error" : "info");

                if ($("#toast").is(":hidden")) {
                    $("#toast")
                        .fadeIn()
                        .delay(8000)
                        .fadeOut("slow");
                }
            }
        },
        "subscribe": function(parentFolder) {
            var url = prompt(_l("Site or feed URL:"));
            if (url) {
                if (url.indexOf("http://") != 0 && url.indexOf("https://") != 0)
                    url = `http://${url}`;

                if (!parentFolder)
                    parentFolder = getRootSubscription();

                parentFolder.subscribe(url);
            }
        },
        "rename": function(subscription) {
            var newName = prompt(_l("New name:"), subscription.title);
            if (newName && newName != subscription.title)
                subscription.rename(newName);
        },
        "createFolder": function() {
            var title = prompt(_l("Name of folder:"));
            if (title) {
                $.ajax({
                    url: "createFolder",
                    type: "POST",
                    data: JSON.stringify({
                        "title": title,
                    }),
                    contentType: "application/json; charset=utf-8",
                    dataType: "json",
                    success: function(response) {
                        resetSubscriptionDom(response.subscriptions, false);
                    }
                });
            }
        },
        "unsubscribe": function(subscription) {
            if (confirm(_l("Unsubscribe from %1$s?", [subscription.title])))
                subscription.unsubscribe();
        },
        "markAllAsRead": function() {
            var subscription = getSelectedSubscription();
            if (subscription == null ||
                subscription.unread < 1 ||
                !subscription.supportsAggregateActions()) {
                return;
            }

            if (subscription.unread > 10 &&
                !confirm(_l("Mark %1$s messages as read?", [subscription.unread]))) {
                return;
            }

            subscription.markAllAsRead();
        },
        "removeFolder": function(folder) {
            if (!confirm(_l("You will be unsubscribed from all subscriptions in this folder. Delete %1$s?", [folder.title])))
                return;

            folder.remove();
        },
        "deleteTag": function(tag) {
            if (!confirm(_l("Tag \"%1$s\" will be removed from all matching articles. Continue?", [tag.title])))
                return;

            tag.remove();
        },
        "removeSubscriptionEntries": function(subscription) {
            $("#gofr-entries .gofr-entry").each(function() {
                var $entry = $(this);
                var entry = $entry.data("entry");

                if (entry.source == subscription.id)
                    $entry.remove();
            });
        },
        "pruneDeadEntries": function() {
            $("#gofr-entries .gofr-entry").each(function() {
                var $entry = $(this);
                var entry = $entry.data("entry");

                if (!subscriptionMap[entry.source])
                    $entry.remove();
            });

            this.onEntryListUpdate();
        },
        "onEntryListUpdate": function() {
            var $centerMessage = $(".center-message");
            if ($("#gofr-entries .gofr-entry").length)
                $centerMessage.hide();
            else {
                // List of entries is empty
                $centerMessage.empty();
                $(".next-page").remove();

                if ($(".subscription").length <= 1) {
                    // User has no subscriptions (root node doesn't count)
                    $centerMessage
                        .append($("<p />")
                            .text(_l("You have not subscribed to any feeds.")))
                        .append($("<p />")
                            .append($("<a />", { "href": "#" })
                                .text(_l("Subscribe"))
                                .click(function() {
                                    ui.subscribe();
                                    return false;
                                }))
                            .append($("<span />")
                                .text(_l(" or ")))
                            .append($("<a />", { "href": "#" })
                                .text(_l("Import subscriptions"))
                                .click(function() {
                                    ui.showImportSubscriptionsModal();
                                    return false;
                                })));
                } else {
                    // User has at least one (non-root) subscription
                    $centerMessage
                        .append($("<p />")
                            .text(_l("No items are available for the current view.")));

                    if (!$("#menu-filter").isSelected(".menu-all-items")) {
                        // Something other than "All items" is selected
                        // Show a toggle link
                        $centerMessage
                            .append($("<p />")
                                .append($("<a />", { "href" : "#" })
                                    .text(_l("Show all items"))
                                    .click(function() {
                                        var selectedSubscription = getSelectedSubscription();
                                        if (selectedSubscription != null) {
                                            $("#menu-filter").selectItem(".menu-all-items");
                                            $("#menu-view").selectItem(".menu-all-items");
                                            selectedSubscription.refresh();
                                        }

                                        return false;
                                    })));
                    }
                }

                $centerMessage.show();
            }
        },
        "localizeStatics": function() {
            $("._l").each(function() {
                var $el = $(this);
                if ($el.text())
                    $el.html(function(index, text) { return _l(text); });
                if ($el.attr("title"))
                    $el.attr("title", function(index, value) { return _l(value); });
            });
        },
        "share": function($anchor) {
            window.open($anchor.attr("href"), "share", $anchor.attr("data-flags"));
            return false;
        },
        "unfloatAll": function() {
            $(".shortcuts").hide();
            ui.toggleNavBar(false);
            $$menu.hideAll();
        },
        "editTags": function(entry) {
            const currentTags = entry.tags.join(", ");
            const enteredTags = prompt(
                _l("Separate multiple tags with commas"),
                currentTags
            );
            if (enteredTags != null && enteredTags != currentTags) {
                $.ajax({
                    url: "setTags",
                    type: "POST",
                    data: JSON.stringify({
                        "articleId": entry.id,
                        "tags": enteredTags
                            .split(",")
                            .map(x => x.trim())
                            .filter(x => x),
                        }),
                    contentType: "application/json; charset=utf-8",
                    dataType: "json",
                    success: function(response) {
                        resetSubscriptionDom(response.subscriptions, false);
                        entry.tags = response.tags;
                        entry.syncView();
                    }
                });
            }
        },
        "onScopeChanged": function() {
            var subscription = getSelectedSubscription();
            if (subscription != null) {
                $(".mark-all-as-read").toggleClass("unavailable",
                    !subscription.supportsAggregateActions());
                $(".filter").toggleClass("unavailable",
                    !subscription.supportsPropertyFilters());
                $(".view-button").toggleClass("unavailable",
                    !subscription.supportsPropertyFilters());

                ui.updateUnreadCount();
            }
        }
    };

    var getRootSubscription = function() {
        if ($(".subscription.root").length > 0)
            return $(".subscription.root").data("subscription");

        return null;
    };

    var getSelectedSubscription = function() {
        if ($(".subscription.selected").length > 0)
            return $(".subscription.selected").data("subscription");

        return null;
    };

    var generateSubscriptionMap = function(userSubs) {
        var map = { "": [] };
        var fmap = { };
        var idCounter = 0;

        userSubs.folders.push({
            "id": "",
        });

        // Create a combined list of folders & subscriptions
        $.each(userSubs.folders, function(index, folder) {
            folder.domId = `sub-${idCounter++}`;
            folder.link = null;
            folder.unread = 0;

            // Inject methods
            for (var name in folderMethods)
                folder[name] = folderMethods[name];

            if (folder.isRoot())
                folder.title = _l("All items");

            if (!map[folder.id])
                map[folder.id] = [];

            fmap[folder.id] = folder;
            map[""].push(folder);
        });

        userSubs.tags.sort(function(a, b) {
            var aTitle = a.title.toLowerCase();
            var bTitle = b.title.toLowerCase();

            if (aTitle < bTitle)
                return -1;
            else if (aTitle > bTitle)
                return 1;

            return 0;
        });

        $.each(userSubs.tags, function(index, tag) {
            tag.id = tag.domId = `tag-${idCounter++}`;

            // Inject methods
            for (var name in tagMethods)
                tag[name] = tagMethods[name];
        });

        var root = fmap[""];
        $.each(userSubs.subscriptions, function(index, subscription) {
            subscription.domId = `sub-${idCounter++}`;

            for (var name in subscriptionMethods)
                subscription[name] = subscriptionMethods[name];

            if (!subscription.parent)
                map[""].push(subscription);
            else {
                fmap[subscription.parent].unread += subscription.unread;
                map[subscription.parent].push(subscription);
            }

            root.unread += subscription.unread;
        });

        $.each(map, function(parentId, children) {
            // Sort the list of children by title
            children.sort(function(a, b) {
                var aTitle = a.title.toLowerCase();
                var bTitle = b.title.toLowerCase();

                if (a.isRoot())
                    return -1;
                else if (b.isRoot())
                    return 1;

                if (aTitle < bTitle)
                    return -1;
                else if (aTitle > bTitle)
                    return 1;

                return 0;
            });
        });

        delete fmap;

        return map;
    };

    var resetSubscriptionDom = function(userSubscriptions, reloadItems) {
        var selectedSubscription = getSelectedSubscription();
        var selectedSubscriptionId = null;

        if (selectedSubscription != null)
            selectedSubscriptionId = selectedSubscription.id;

        // Special folders
        specialFolders = [{
            "id":     "sf-liked",
            "domId":  "sf-liked",
            "type":   "liked",
            "title":  _l("Liked items"),
            "filter": { "prop": "like" },
        }, {
            "id":    "sf-starred",
            "domId": "sf-starred",
            "type":  "starred",
            "title": _l("Starred items"),
            "filter": { "prop": "star" },
        }];

        $.each(specialFolders, function(index, specialFolder) {
            // Inject methods
            for (var name in specialFolderMethods)
                specialFolder[name] = specialFolderMethods[name];
        });

        var collapsedFolderIds = [];
        $.each($("#subscriptions .folder-collapsed"), function() {
            var $subscription = $(this).closest(".subscription");
            var subscription = $subscription.data("subscription");

            collapsedFolderIds.push(subscription.id);
        });

        var $newSubscriptions = $("<ul />", { "id": "subscriptions" });
        var newSubscriptionMap = {};
        var newSubscriptions = [];
        var markedFirstSub = false;

        const faviconless = $.map($(".subscription-icon.no-favicon").closest(".subscription:not(.folder)"), function(e) {
            return $(e).data("subscription").id;
        });
        var subMap = generateSubscriptionMap(userSubscriptions);
        var createSubDom = function(subscription) {
            const url = URL.parse(subscription.link);
            var favicon = transparentIcon;
            if (url && $.inArray(subscription.id, faviconless) == -1) {
                url.pathname = "/favicon.ico";
                favicon = url.toString();
            }
            var $subscription = $("<li />", { "class" : `subscription ${subscription.domId}` })
                .data("subscription", subscription)
                .append($("<div />", { "class" : "subscription-item" })
                    .append($("<span />", { "class" : "chevron" })
                        .click(function(e) {
                            var $menu = $(`#menu-${subscription.getType()}`);
                            $menu.openMenu(e.pageX, e.pageY, subscription.id);
                            e.stopPropagation();
                        }))
                    .append(
                        $("<img />", {
                            "class" : `subscription-icon${favicon == transparentIcon ? " no-favicon" : ""}`,
                            "src": favicon,
                        })
                        .one("error", function() {
                            $(this)
                                .attr("src", transparentIcon)
                                .addClass("no-favicon");
                        })
                    )
                    .append(
                        $("<a />", {
                            "class" : "subscription-title",
                            "href" : subscription.link,
                            "target" : "_blank",
                        })
                            .text(subscription.title)
                            .click(function(e) {
                                e.preventDefault();
                            })
                    )
                    .attr("title", subscription.title)
                    .append($("<span />", { "class" : "subscription-unread-count" }))
                    .click(function() {
                        subscription.select();
                    }));

            if (!subscription.isFolder()) {
                // Drag-and-drop code
                $subscription
                    .mousedown(function(e) {
                        if (e.which != 1)
                            return;

                        var $elem = $(document.elementFromPoint(e.pageX, e.pageY)).closest(".subscription");
                        if (!$elem.length)
                            return;

                        $("#subscriptions").mousemove(function(e) {
                            if (!$dragSource) {
                                $dragSource = $elem;
                                $dragSource.addClass("dragged");
                                $dragClone = $dragSource.clone().removeClass("dragged").addClass("dragging");
                                dragDestination = null;

                                return;
                            }

                            var dragSource = $dragSource.data("subscription");
                            var $hoveredElement = $(document.elementFromPoint(e.pageX, e.pageY));

                            if ($hoveredElement) {
                                var $sub = $hoveredElement.closest(".subscription");
                                var sub = $sub.data("subscription");

                                var $newParent = null;
                                var newParentId = null;

                                if ($sub.is("li.folder")) {
                                    $newParent = $sub.children("ul:first");
                                    newParentId = sub.id;
                                    dragDestination = sub;
                                } else if (sub != null) {
                                    $newParent = $sub.closest("ul");
                                    newParentId = sub.parent;
                                    dragDestination = subscriptionMap[sub.parent || ""];
                                } else {
                                    return false;
                                }

                                $("#subscriptions .dragging").remove();

                                if (newParentId != dragSource.parent) {
                                    var $followingElement = null;

                                    $newParent.children("li").each(function() {
                                        var $child = $(this);
                                        var child = $child.data("subscription");

                                        if (dragSource.title.toUpperCase() < child.title.toUpperCase()) {
                                            $followingElement = $child;
                                            return false;
                                        }
                                    });

                                    if ($followingElement != null)
                                        $dragClone.insertBefore($followingElement);
                                    else
                                        $dragClone.appendTo($newParent);
                                }
                            }
                        });

                        return false;
                    });
            } else /* if (subscription.isFolder()) */ {
                if (!subscription.isRoot()) {
                    $subscription.find(".subscription-item")
                        .append($("<span />", { "class" : "folder-toggle" })
                            .click(function(e) {
                                var $toggleIcon = $(this);
                                $toggleIcon.toggleClass("folder-collapsed");
                                if ($toggleIcon.hasClass("folder-collapsed"))
                                    $subscription.find("ul").slideUp("fast");
                                else
                                    $subscription.find("ul").slideDown("fast");

                                return false;
                            })
                            .toggleClass("folder-collapsed", $.inArray(subscription.id, collapsedFolderIds) > -1));
                }
            }

            if (!subscription.isRoot() && !markedFirstSub) {
                $subscription.addClass("first");
                markedFirstSub = true;
            }

            return $subscription.addClass(subscription.getType());
        };

        var buildDom = function($parent, subscriptions) {
            $.each(subscriptions, function() {
                var subscription = this;
                var $subscription = createSubDom(subscription);

                $parent.append($subscription);
                if (subscription.id) {
                    var children = subMap[subscription.id];
                    if (children) {
                        var $child = $("<ul />");
                        if ($.inArray(subscription.id, collapsedFolderIds) > -1)
                            $child.hide();

                        $subscription.append($child);

                        buildDom($child, children);
                    }
                }

                newSubscriptionMap[subscription.id] = subscription;
                newSubscriptions.push(subscription);

                if (selectedSubscriptionId == subscription.id)
                    selectedSubscription = subscription;
                else if (selectedSubscriptionId == null) {
                    if (subscription.isFolder() && subscription.isRoot())
                        selectedSubscription = subscription;
                }
            });
        };

        buildDom($newSubscriptions, subMap[""]);

        var $appendAfter = $newSubscriptions.find(".root.subscription");
        var firstClass = "first";

        $.each(specialFolders, function(_, specialFolder) {
            var $specialFolder = $("<li />", { "class" : `subscription special-folder ${specialFolder.domId} ${firstClass}` })
                .data("subscription", specialFolder)
                .append($("<div />", { "class" : "subscription-item" })
                    .append($("<img />", {
                        "class" : "subscription-icon",
                        "src": transparentIcon,
                    }))
                    .append($("<span />", { "class" : "subscription-title" })
                        .text(specialFolder.title))
                    .attr("title", specialFolder.title)
                    .click(function() {
                        specialFolder.select();
                    }));

            $appendAfter.after($specialFolder);

            firstClass = "";
            $appendAfter = $specialFolder;
        });

        firstClass = "first";
        $.each(userSubscriptions.tags, function(_, tag) {
            var $tag = $("<li />", { "class" : `subscription tag ${tag.domId} ${firstClass}` })
                .data("subscription", tag)
                .append($("<div />", { "class" : "subscription-item" })
                    .append($("<span />", { "class" : "chevron" })
                        .click(function(e) {
                            var $menu = $("#menu-tag");
                            $menu.openMenu(e.pageX, e.pageY, tag.id);
                            e.stopPropagation();
                        }))
                    .append($("<img />", {
                        "class" : "subscription-icon",
                        "src": transparentIcon,
                    }))
                    .append($("<span />", { "class" : "subscription-title" })
                        .text(tag.title))
                    .attr("title", tag.title)
                    .click(function() {
                        tag.select();
                    }));

            firstClass = "";
            $newSubscriptions.append($tag);
        });

        $("#subscriptions").replaceWith($newSubscriptions)

        subscriptionMap = newSubscriptionMap;

        $("body").toggleClass("sidebar-hidden", true);

        $.each(newSubscriptions, function() {
            this.syncView();
        });

        $("body").toggleClass("sidebar-hidden", false);

        ui.updateUnreadCount();
        selectedSubscription.select(reloadItems);
    };

    var refresh = function(reloadItems) {
        $.ajax({
            url: "subscriptions",
            data: {},
            dataType: "json",
            success: function(response) {
                resetSubscriptionDom(response, reloadItems);
            }
        });
    };

    var syncFeeds = function() {
        (function feedUpdater() {
            console.debug("Updating feeds...");
            const now = new Date().getTime();
            const delta = now - lastRefresh;

            if (delta < 60000) {
                console.debug(`Ignoring sync request (last sync ${delta / 1000}s ago)`);
                return; // No need to sync yet
            }

            if (timeoutId > -1) {
                clearTimeout(timeoutId);
                timeoutId = -1;
            }

            console.debug(`Synchronizing feeds (last sync ${delta / 1000}s ago)`);
            lastRefresh = now;

            $.ajax({
                url: "syncFeeds",
                type: "POST",
                data: JSON.stringify({}),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function(response) {
                    if (console && console.debug) {
                        console.debug(`Next sync: ${response.nextSync}`);
                    }
                }
            })
            .always(function() {
                timeoutId = setTimeout(feedUpdater, 600000); // 10 minutes
            });
        })();
    };

    const socket = io();
    socket
        .on("connect", function() {
            console.debug("Connected");
        })
        .on("refresh", function(response) {
            console.debug(`Refresh received: ${response}`);
            refresh(response != null && response.includes("articles"));
        });

    ui.init();

    refresh();
});
