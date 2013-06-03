(function() {
"use strict";
window.APP=window.APP||{Routers:{},Collections:{},Models:{},Views:{}};

APP.Views.Reader = Backbone.View.extend({
    _rendered: false,
    _renderLeftSide: function() {
        this.$el.find('#feed-list').load('/raven/_feedlist/');
    },
    _renderRightSide: function() {
        var view = new APP.Views.FeedItemListView({items: this.items});
        this.$el.find('#strong-side').html(view.render().el);
    },
    addFeed: function(e) {
        e.preventDefault();
        var url = $('#add-feed').val();
        var urlregex = new RegExp(
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
        $('#add-feed').val('');
    },
    deleteFeed: function(e) {
        /* TODO: we should really pop up a "confirm"-type box. */
        e.preventDefault();
        var target = $(e.target).parent().parent(),
            feedID = target.attr('data-feedid'),
            feed = this.feeds.where({id: parseInt(feedID, 10)})[0];
        feed.destroy({
            success: function(model, response) {
                target.remove();
            }
        });
    },
    el: '#main',
    events: {
        'click button#add-feed': 'addFeed',
        'click div.delete-feed': 'deleteFeed'
    },
    initialize: function(options) {
        /* Disabled for now.
        this.feeds = new APP.Collections.Feeds();
         */
    },
    render: function() {
        if (this._rendered) { return this; }

        var template = Handlebars.compile($('#index-template').html());
        this.$el.html(template);

        /* Disabled for now.
        this.feeds.fetch({success: this.feeds.onSuccess});
         */
        this._renderLeftSide();

        this._rendered = true;
        return this;
    },
    setFeed: function(id) {
        this.feed = undefined;
        this.items = undefined;
        this.$el.find('#strong-side').empty();

        if (!id) {
            this.items = new APP.Collections.FeedItems();

            this.items.on('reset', function() {
                this._renderRightSide();
            }, this);
            this.items.fetch({reset: true, success: this.items.onSuccess});
        } else {
            /* This motherfucking bullshit right here is because
             * motherfucking Backbone fucking Relational doesn't modify
             * Collection to pull for the Store.
             */
            /* Disabled for now.
            this.feed = this.feeds.where({id: parseInt(id, 10)})[0];
            if (!this.feed) {
                this.feed = APP.Models.Feed.findOrCreate({id: id});
            }
            */

            this.feed = APP.Models.Feed.findOrCreate({id: id});
            this.feed.once('sync', _.bind(function(__) {
                this.items = this.feed.get('items');
                this.items.once('sync', _.bind(function(__) {
                    this._renderRightSide();
                }, this));
                this.feed.fetchRelated('items');
            }, this));
            this.feed.fetch();
        }
    }
});

$.fn.isOnScreen = function(){
    /* Convenience method for checking to see if a node is in the viewport. */
    var win = $(window);

    var viewport = {
        top : win.scrollTop(),
        left : win.scrollLeft()
    };
    viewport.right = viewport.left + win.width();
    /* HACK! We only want the top quarter to trigger the event... */
    viewport.bottom = viewport.top + (win.height() * .25);

    var bounds = this.offset();
    if (bounds === undefined) { return; }

    bounds.right = bounds.left + this.outerWidth();
    bounds.bottom = bounds.top + this.outerHeight();

    return (!(viewport.right < bounds.left || viewport.left > bounds.right ||
              viewport.bottom < bounds.top || viewport.top > bounds.bottom));
};

APP.Views.FeedItemListView = Backbone.View.extend({
    _add: function(item) {
        this._renderItem(item);
        this._loader.show();
    },
    _more: function(e) {
        e.preventDefault();

        if (this.items.hasNext()) {
            this.items.getNext();
        }
        this._loader.hide();
    },
    _remove: function(e) {
        /* TODO: implement this? */
    },
    _renderItem: function(item) {
        var view = new APP.Views.FeedItemView({item: item}),
            container = this.$el.find('#feeditem-container');
        container.append(view.render().el);
    },
    _scrollLast: 0,
    _currentRow: null,
    _scroll: function(e) {
        var selected = this._currentRow.find('.feeditem'),
            nextSelected = null,
            nextRow = null,
            headline = null,
            nextHeadline = null,
            item = null;

        var scrollPosition = $(e.currentTarget).scrollTop();
        /* Scroll down */
        if (scrollPosition > this._scrollLast) {
            selected.addClass('selected');
            item = this.items.get(this._currentRow.attr('data-feeditem'));
            if (item.attributes.read === false) {
                item.save({'read': true});
            }

            headline = selected.find('h3');
            nextRow = this._currentRow.next('div.row');
            nextSelected = nextRow.find('.feeditem');
            nextHeadline = nextSelected.find('h3');

            if (nextHeadline.isOnScreen() && !headline.isOnScreen()) {
                selected.removeClass('selected');
                nextSelected.addClass('selected');
                item = this.items.get(nextRow.attr('data-feeditem'));
                if (item.attributes.read === false) {
                    item.save({'read': true});
                }

                this._currentRow = nextRow;
            }
        /* Scroll up */
        } else if (scrollPosition < this._scrollLast) {
            headline = selected.find('h3');
            nextRow = this._currentRow.prev('div.row');
            nextSelected = nextRow.find('.feeditem');

            if (nextRow.length === 0) {
                this._scrollLast = scrollPosition;
                return;
            }

            if (!headline.isOnScreen() && nextRow.isOnScreen()) {
                selected.removeClass('selected');
                nextSelected.addClass('selected');

                this._currentRow = nextRow;
            }
        }
        this._scrollLast = scrollPosition;
    },
    _keyNav: function(e, combo) {
        var selected = this._currentRow.find('.feeditem'),
            headline = selected.find('h3'),
            nextSelected = null,
            nextRow = null,
            nextHeadline = null,
            scrollTarget = 0;

        if (combo === 'j' || combo === 'n') {
            nextRow = this._currentRow.next('div.row');
        } else if (combo === 'k' || combo === 'p') {
            // This little bit allows us to scroll to top of current
            // feeditem if we are in the middle of it, rather than going
            // all the way to the previous feeditem (which would be
            // jarring and weird).
            if (!headline.isOnScreen()) {
                nextRow = this._currentRow;
            } else {
                nextRow = this._currentRow.prev('div.row');
            }
        }

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
        scrollTarget = this._scrollLast + nextHeadline.offset().top - 63;

        $('#strong-side').animate({
            scrollTop: scrollTarget
        }, 1, function () {
            selected.removeClass('selected');
            nextSelected = nextRow.find('.feeditem');
            nextSelected.addClass('selected');
        });

        this._currentRow = nextRow;
    },
    initialize: function(options) {
        this.items = options.items;

        this.items.on('add', _.bind(this._add, this));
        this.items.on('remove', _.bind(this._remove, this));
        this.items.on('reset sort', _.bind(this.render, this));

        // Keybindings!
        Mousetrap.bind(['j', 'n', 'k', 'p'], _.bind(this._keyNav, this));
    },
    render: function() {
        $('#strong-side').scroll(_.bind(this._scroll, this));

        var el = this.$el,
            template = Handlebars.compile($('#feed-item-list-template').html());
        el.html(template({}));
        this._loader = el.find('.feeditem-loader');

        el.find('#loader').click(_.bind(this._more, this));

        var container = el.find('#feeditem-container');
        container.children().remove();
        _.each(this.items.models, _.bind(function(item) {
            this._renderItem(item);
        }, this));

        this._currentRow = el.find('#feeditem-container div.row').first();

        return this;
    }
});

APP.Views.FeedItemView = Backbone.View.extend({
    _render: function() {
        var template = Handlebars.compile($('#feed-item-template').html());
        var context = {
            feed: this.item.get('feed').attributes,
            item: this.item.attributes
        };
        this.$el.html(template(context));
        this.$el.find('a').attr('target', '_blank');
    },
    className: 'row',
    initialize: function(options) {
        this.item = options.item;
        this.$el.attr('data-feeditem', this.item.id);
    },
    render: function() {
        if (this.item.get('title') !== undefined) {
            this._render();
        } else {
            this.item.on('change', function() {
                this._render();
            }, this);
            this.item.fetch();
        }

        return this;
    }
});

}());
