(function() {
"use strict";
window.APP=window.APP||{Routers:{},Collections:{},Models:{},Views:{}};

APP.Views.LeftSide = Backbone.View.extend({
    addFeed: function(e) {
        e.preventDefault();
        return;

        /* TODO: Implement this properly */
        var addFeedForm = this.$el.find(this.addFeedFormEl),
            url = addFeedForm.val(),
            urlregex = new RegExp(
                "^(http:\/\/|https:\/\/|ftp:\/\/){1}([0-9A-Za-z]+)");
        if (urlregex.test(url)) {
            console.log('adding feed for '+url);
            var feed = new APP.Models.Feed({
                link: url
            });
            feed.save();
            this.feeds.add(feed);
        } else {
            // TODO: handle the error
            console.log('not a url');
        }
        addFeedForm.val('');
    },
    addFeedFormEl: '#add-feed',
    el: '#left-side',
    events: {
        'click button#add-feed-btn': 'addFeed'
    },
    feedListEl: '#feed-list',
    initialize: function(config) {
        /* TODO: get feeds and add event listeners. */
    },
    render: function() {
        this.$el.find(this.feedListEl).load('/raven/_feedlist/');
        this.rendered = true;
        return this;
    }
});

$.fn.isOnScreen = function(loc){
    /* Convenience method for checking to see if a node is in the viewport. */
    var win = $(window);

    var viewport = {
        top : win.scrollTop(),
        left : win.scrollLeft()
    };
    viewport.right = viewport.left + win.width();
    if (loc === 'bottom' ) {
        viewport.bottom = viewport.top + win.height();
    } else {
        /* HACK! We only want the top quarter to trigger the event... */
        viewport.bottom = viewport.top + (win.height() * .25);
    }

    var bounds = this.offset();
    if (bounds === undefined) { return; }

    bounds.right = bounds.left + this.outerWidth();
    bounds.bottom = bounds.top + this.outerHeight();

    return (!(viewport.right < bounds.left || viewport.left > bounds.right ||
              viewport.bottom < bounds.top || viewport.top > bounds.bottom));
};

APP.Views.StrongSide = Backbone.View.extend({
    add: function(item) {
        this.renderItem(item);
    },
    containerEl: '#feeditem-container',
    currentRow: null,
    infiniteLoader: null,
    el: '#strong-side',
    events: {
        'click .feeditem': 'select_and_read',
        'click .feeditem-loader': 'more',
        'scroll': 'scroll_'
    },
    filter: function(config) {
        /* Take a config of feed and/or tag, and add them as filters, and
         * reset the items.
         */
        this.$el.find(this.containerEl).empty();
        if (config.feed) {
            this.items.params.feed = config.feed;
        } else {
            if (this.items.params.feed != undefined) {
                delete this.items.params.feed;
            }
        }
        if (config.tag) {
            this.items.params.tag = config.tag;
        } else {
            if (this.items.params.tag != undefined) {
                delete this.items.params.tag;
            }
        }
        this.items.params.offset = 0;
        this.items.fetch({reset: true, success: this.items.success});
    },
    initialize: function(config) {
        config = config||{};

        Mousetrap.bind(['j', 'n', 'k', 'p'], _.bind(this.keys, this));

        this.items = new APP.Collections.Items();
        this.items.on('add', _.bind(this.add, this));
        this.items.on('reset', _.bind(this.render, this));

        var params = config.params||{};
        this.filter(params);
    },
    keys: function(e, combo) {
        var selected = this.select_and_read(e),
            headline = selected.find('h3'),
            nextSelected = null,
            nextRow = null,
            nextHeadline = null,
            scrollTarget = 0,
            el = this.$el;

        if (combo === 'j' || combo === 'n') {
            nextRow = this.currentRow.next('div.row');
        } else if (combo === 'k' || combo === 'p') {
            // This little bit allows us to scroll to top of current
            // feeditem if we are in the middle of it, rather than going
            // all the way to the previous feeditem (which would be
            // jarring and weird).
            if (!headline.isOnScreen()) {
                nextRow = this.currentRow;
            } else {
                nextRow = this.currentRow.prev('div.row');
            }
        }

        /* TODO: Remove this and actually fix your damn code. */
        if (nextRow.length === 0) { return; }

        // We need to adjust the offset by the height of the current
        // headline, which can be calculated as show below. This value
        // is currently 63px.
        //
        // For some reason, trying to calculate it dynamically results
        // in our math being off, and scrolling to the wrong place on
        // the page, so hard code it and fix as necessary if we ever
        // change the size of the headline.
        //var headline = selected.find('h3');
        //console.log(headline.offset().top);

        // Calculate next offset
        nextHeadline = nextRow.find('h3');
        scrollTarget = this.scrollLast + nextHeadline.offset().top - 63;

        el.animate({
            scrollTop: scrollTarget
        }, 1, function () {
            selected.removeClass('selected');
            nextSelected = nextRow.find('.feeditem');
            nextSelected.addClass('selected');
        });

        this.currentRow = nextRow;
    },
    more: function(e) {
        e.preventDefault();
        this.items.getNext();
    },
    select_and_read: function(e) {
        var selected = null,
            item = null,
            item2 = null;

        switch (e.type) {
        case 'click':
            selected = $(e.currentTarget);
            break;
        case 'scroll':
        case 'keypress':
            selected = this.currentRow.find('.feeditem');
            break;
        }

        selected.addClass('selected');
        item = this.items.get(selected.parent().attr('data-feeditem'));

        /* This happens when loading more items, the old items go out of
         * scope and we'll get something undefined. Just return the
         * current selected item.
         */
        if (item == undefined) {
            return selected;
        }
        if (item.attributes.read === false) {
            item.save({'read': true});
        }

        /* No idea why selected === this.currentRow => false */
        item2 = this.items.get(this.currentRow.attr('data-feeditem'));
        if (!_.isEqual(item, item2)) {
            var prevSelected = this.currentRow.find('.feeditem');
            prevSelected.removeClass('selected');
            this.currentRow = selected.parent();
        }

        return selected;
    },
    render: function() {
        var el = this.$el;
        el.html(this.template());

        var container = el.find(this.containerEl);
        container.children().remove();
        if (this.items.length == 0) {
            this.$el.html(this.templateEmpty());
        } else {
            _.each(this.items.models, _.bind(function(item) {
                this.renderItem(item);
            }, this));

            /* What we should do is keep track of objects, and allow data
             * binding to set selected.
             */
            this.currentRow = container.find('div.row').first();
            this.infiniteLoader = container.next('div.feeditem-loader');
        }
        return this;
    },
    renderItem: function(item) {
        var view = new ItemView({item: item}),
            container = this.$el.find(this.containerEl);
        container.append(view.render().el);
    },
    scroll_: function(e) {
        var selected = this.select_and_read(e),
            nextSelected = null,
            nextRow = null,
            headline = null,
            nextHeadline = null,
            item = null;

        var scrollPosition = $(e.currentTarget).scrollTop();
        /* Scroll down */
        if (scrollPosition > this.scrollLast) {
            headline = selected.find('h3');
            nextRow = this.currentRow.next('div.row');
            nextSelected = nextRow.find('.feeditem');
            nextHeadline = nextSelected.find('h3');

            if (nextHeadline.isOnScreen() && !headline.isOnScreen()) {
                selected.removeClass('selected');
                nextSelected.addClass('selected');
                item = this.items.get(nextRow.attr('data-feeditem'));
                if (item.attributes.read === false) {
                    item.save({'read': true});
                }

                this.currentRow = nextRow;
            }

            if (this.infiniteLoader.isOnScreen('bottom')) {
                this.more(e);
            }

        /* Scroll up */
        } else if (scrollPosition < this.scrollLast) {
            headline = selected.find('h3');
            nextRow = this.currentRow.prev('div.row');
            nextSelected = nextRow.find('.feeditem');

            if (nextRow.length === 0) {
                this.scrollLast = scrollPosition;
                return;
            }

            if (!headline.isOnScreen() && nextRow.isOnScreen()) {
                selected.removeClass('selected');
                nextSelected.addClass('selected');

                this.currentRow = nextRow;
            }
        }
        this.scrollLast = scrollPosition;
    },
    scrollLast: 0,
    template: Handlebars.compile($('#feed-item-list-template').html()),
    templateEmpty: Handlebars.compile($('#feed-item-empty-template').html())
});

var ItemView = Backbone.View.extend({
    className: 'row',
    initialize: function(config) {
        this.item = config.item;
        this.$el.attr('data-feeditem', this.item.id);
    },
    render: function() {
        var el = this.$el,
            context = {
                feed: this.item.get('feed').attributes,
                item: this.item.attributes
            };
        el.html(this.template(context));
        el.find('.content a').attr('target', '_blank');
        return this;
    },
    template: Handlebars.compile($('#feed-item-template').html())
});

}());
