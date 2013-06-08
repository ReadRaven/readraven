(function() {
"use strict";
window.APP=window.APP||{Routers:{},Collections:{},Models:{},Views:{}};

APP.Views.AddFeedModal = Backbone.View.extend({
    addFeed: function(e) {
        e.preventDefault();

        var url = this.$el.find(this.feedInputEl).val(),
            urlregex = new RegExp(
                "^(http:\/\/|https:\/\/|ftp:\/\/){1}([0-9A-Za-z]+)");
        if (urlregex.test(url)) {
            console.log('adding feed for '+url);
            var feed = new APP.Models.Feed({
                link: url
            });
            feed.save();

            this.undelegateEvents();
            this.remove();
            Backbone.View.prototype.remove.call(this);
        } else {
            // TODO: handle the error
            console.log('not a url');
        }
    },
    className: 'modal',
    events: {
        'click button.notice': 'addFeed'
    },
    feedInputEl: '#feed-url',
    render: function() {
        var el = this.$el;
        el.html(this.template());
        $('body').prepend(el);
    },
    template: Handlebars.compile($('#add-feed-modal').html())
});

APP.Views.LeftSide = Backbone.View.extend({
    addFeed: function(e) {
        e.preventDefault();

        var view = new APP.Views.AddFeedModal();
        view.render();
    },
    addFeedFormEl: '#add-feed',
    el: '#left-side',
    events: {
        'click a#add-feed-btn': 'addFeed'
    },
    feedListEl: '#feed-list',
    initialize: function(config) {
        /* TODO: get feeds and add event listeners. */
    },
    render: function() {
        /* While we have two sets of UI, this is an agreeable workaround. */
        if (window.location.pathname.indexOf('home') > -1) {
            this.$el.load('/raven/_feedlist/');
        } else {
            this.$el.load('/reader/leftside/');
        }
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
    if (loc === 'infinite' ) {
        viewport.bottom = viewport.top + win.height() + 200;
    } else {
        /* HACK! We only want the top quarter to trigger the event... */
        viewport.bottom = viewport.top + (win.height() * 0.25);
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
        'click .feeditem-content': 'select_and_read',
        'click .feeditem-loader': 'more'
    },
    filter: function(config) {
        /* Take a config of feed and/or tag, and add them as filters, and
         * reset the items.
         */
        this.$el.find(this.containerEl).empty();
        if (config.feed) {
            this.items.params.feed = config.feed;
        } else {
            if (this.items.params.feed !== undefined) {
                delete this.items.params.feed;
            }
        }
        if (config.tag) {
            this.items.params.tag = config.tag;
        } else {
            if (this.items.params.tag !== undefined) {
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
            headline = selected.find('h1'),
            nextSelected = null,
            nextRow = null,
            nextHeadline = null,
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

        $('body').animate({
            scrollTop: nextRow.offset().top - 20 /* Podding of window */
        }, 1, 'swing', _.bind(function () {
            selected.removeClass('selected');
            nextRow.find('.feeditem-content').addClass('selected');
            this.currentRow = nextRow;
        }, this));

    },
    more: function(e) {
        e.preventDefault();
        this.items.getNext();
    },
    render: function() {
        $(window).scroll(_.bind(this.scroll_, this));

        var el = this.$el;
        el.html(this.template());

        var container = el.find(this.containerEl);
        container.children().remove();
        if (this.items.length === 0) {
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
            headline = selected.find('h1');
            nextRow = this.currentRow.next('div.row');
            nextSelected = nextRow.find('.feeditem-content');
            nextHeadline = nextSelected.find('h1');

            if (nextHeadline.isOnScreen() && !headline.isOnScreen()) {
                selected.removeClass('selected');
                nextSelected.addClass('selected');
                item = this.items.get(nextRow.attr('data-feeditem'));
                if (item.attributes.read === false) {
                    item.save({'read': true});
                }

                this.currentRow = nextRow;
            }

            if (this.infiniteLoader.isOnScreen('infinite')) {
                this.more(e);
            }

        /* Scroll up */
        } else if (scrollPosition < this.scrollLast) {
            headline = selected.find('h1');
            nextRow = this.currentRow.prev('div.row');
            nextSelected = nextRow.find('.feeditem-content');

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
            selected = this.currentRow.find('.feeditem-content');
            break;
        }

        selected.addClass('selected');
        item = this.items.get(selected.parent().attr('data-feeditem'));

        /* This happens when loading more items, the old items go out of
         * scope and we'll get something undefined. Just return the
         * current selected item.
         */
        if (item === undefined) {
            return selected;
        }
        if (item.attributes.read === false) {
            item.save({'read': true});
        }

        /* No idea why selected === this.currentRow => false */
        item2 = this.items.get(this.currentRow.attr('data-feeditem'));
        if (!_.isEqual(item, item2)) {
            var prevSelected = this.currentRow.find('.feeditem-content');
            prevSelected.removeClass('selected');
            this.currentRow = selected.parent();
        }

        return selected;
    },
    template: Handlebars.compile($('#feed-item-list').html()),
    templateEmpty: Handlebars.compile($('#feed-item-empty').html())
});

var ItemView = Backbone.View.extend({
    /* We should kill the 'row' class, but not now... */
    className: 'pure-g feeditem row',
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
    template: Handlebars.compile($('#feed-item').html())
});

}());
