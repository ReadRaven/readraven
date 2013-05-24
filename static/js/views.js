(function() {
"use strict";
window.APP = window.APP || {Routers: {}, Collections: {}, Models: {}, Views: {}};

APP.Views.Reader = Backbone.View.extend({
    _renderLeftBar: function() {
        var view = new APP.Views.FeedListView({feeds: this.feeds});
        this.$el.find('#feed-list').html(view.render().el);
    },
    _renderRightBar: function() {
        var view = new APP.Views.FeedItemListView({items: this.items});
        this.$el.find('#item-list').html(view.render().el);
    },
    addFeed: function(e) {
        e.preventDefault();
        var url = $('#add-feed').val();
        var urlregex = new RegExp(
            "^(http:\/\/|https:\/\/|ftp:\/\/){1}([0-9A-Za-z]+\.)");
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
        e.preventDefault();
        var actualTarget = e.target.parentNode.parentNode,
            feedID = actualTarget.getAttribute('data-feedid'),
            feed = this.feeds.where({id: parseInt(feedID, 10)})[0];
        feed.destroy({
            success: function(model, response) {
                actualTarget.remove();
            }
        });
    },
    el: '#main',
    events: {
        'click button#add-feed': 'addFeed',
        'click div.delete-feed': 'deleteFeed'
    },
    initialize: function(options) {
        if (options.feedID) {
            this.feeds = options.feeds;
            this.feedID = options.feedID;
        } else {
            this.feeds = options.feeds;
            this.items = options.items;
        }
    },
    render: function() {
        var template = Handlebars.compile($('#index-template').html());
        this.$el.html(template);

        if (this.feedID) {
            this.feeds.on('reset', function() {

                this.feed = this.feeds.where({id: parseInt(this.feedID, 10)})[0];
                this.feed.fetchRelated('items');
                this.items = this.feed.get('items');
                this._renderRightBar();
            }, this);
            this.feeds.fetch({reset: true, success: this.feeds.onSuccess});
        } else {
            this.feeds.fetch({reset: true, success: this.feeds.onSuccess});

            this.items.on('reset', function() {
                this._renderRightBar();
            }, this);
            this.items.fetch({reset: true, success: this.items.onSuccess});
        }
        this._renderLeftBar();
        return this;
    }
});

APP.Views.FeedListView = Backbone.View.extend({
    _add: function(feed) {
        this._renderFeed(feed);
    },
    _remove: function(e) {
        /* TODO: implement this? */
    },
    _renderFeed: function(feed) {
        var view = new APP.Views.FeedListingView({feed: feed});
        this.$el.append(view.render().el);
    },
    initialize: function(options) {
        this.feeds = options.feeds;

        this.feeds.on('add', _.bind(this._add, this));
        this.feeds.on('remove', _.bind(this._remove, this));
        this.feeds.on('reset sort', _.bind(this.render, this));
        /* TODO: handle 'change' and 'sync' events. */
    },
    render: function(e) {
        var el = this.$el;
        el.children().remove();
        _.each(this.feeds.models, _.bind(function(feed) {
            this._renderFeed(feed);
        }, this));
        return this;
    }
});

APP.Views.FeedListingView = Backbone.View.extend({
    initialize: function(options) {
        this.feed = options.feed;
    },
    render: function() {
        var template = Handlebars.compile($('#feed-listing-template').html());
        this.$el.html(template(this.feed.attributes));
        return this;
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
    viewport.bottom = viewport.top + win.height();

    var bounds = this.offset();
    bounds.right = bounds.left + this.outerWidth();
    bounds.bottom = bounds.top + this.outerHeight();

    return (!(viewport.right < bounds.left || viewport.left > bounds.right ||
              viewport.bottom < bounds.top || viewport.top > bounds.bottom));
};

APP.Views.FeedItemListView = Backbone.View.extend({
    _add: function(item) {
        this._renderItem(item);
    },
    _remove: function(e) {
        /* TODO: implement this? */
    },
    _renderItem: function(item) {
        var view = new APP.Views.FeedItemView({item: item});
        this.$el.append(view.render().el);
    },
    _scrollLast: 0,
    _scroll: function(e) {
        var selected = $('.feeditem.selected');
        if (selected.length === 0) {
            $('.feeditem').eq(0).addClass('selected');
        } else {
            var par = selected.parent(),
                next_par = null;

            var scrollPosition = $(e.currentTarget).scrollTop();
            if (scrollPosition > this._scrollLast) {
                /* Scroll down */
                next_par = par.next();

                var next = next_par.find('.feeditem'),
                    headline = next.find('h3');
                if (headline.isOnScreen()) {
                    selected.removeClass('selected');
                    next.addClass('selected');
                }
            } else if (scrollPosition < this._scrollLast) {
                /* Scroll up */
                next_par = par.prev();
                if (next_par.length === 0) { return; }

                var next = next_par.find('.feeditem'),
                    headline = selected.find('h3');
                if (!headline.isOnScreen() && next.isOnScreen()) {
                    selected.removeClass('selected');
                    next.addClass('selected');
                }
            }
            this._scrollLast = scrollPosition;
        }
    },
    initialize: function(options) {
        this.items = options.items;

        this.items.on('add', _.bind(this._add, this));
        this.items.on('remove', _.bind(this._remove, this));
        this.items.on('reset sort', _.bind(this.render, this));
    },
    render: function() {
        var el = this.$el;

        $(window).scroll(_.bind(this._scroll, this));

        el.children().remove();
        _.each(this.items.models, _.bind(function(item) {
            this._renderItem(item);
        }, this));

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
    },
    className: 'row',
    initialize: function(options) {
        this.item = options.item;
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
