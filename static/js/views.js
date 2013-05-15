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
    events: {
        'click button#add-feed': 'addFeed'
    },
    initialize: function(options) {
        this.feeds = options.feeds;
        this.items = options.items;
    },
    render: function() {
        var template = Handlebars.compile($('#index-template').html());
        this.$el.html(template);

        this._renderLeftBar();
        this._renderRightBar();

        return this;
    }
});

APP.Views.FeedListView = Backbone.View.extend({
    initialize: function(options) {
        this.feeds = options.feeds;
        this.feeds.bind('add', _.bind(this.render, this));
        this.feeds.bind('remove', _.bind(this.render, this));
    },
    render: function(e) {
        var el = this.$el;
        el.children().remove();
        _.each(this.feeds.models, _.bind(function(feed) {
            var view = new APP.Views.FeedListingView({feed: feed});
            el.append(view.render().el);
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

APP.Views.FeedItemListView = Backbone.View.extend({
    initialize: function(options) {
        this.items = options.items;
    },
    render: function() {
        var el = this.$el;
        el.children().remove();
        _.each(this.items.models, _.bind(function(item) {
            var view = new APP.Views.FeedItemView({item: item});
            el.append(view.render().el);
        }, this));
        return this;
    }
});

APP.Views.FeedItemView = Backbone.View.extend({
    initialize: function(options) {
        this.item = options.item;
        console.log('feeditem initialize');
    },
    render: function() {
        var template = Handlebars.compile($('#feed-item-template').html());
        this.$el.html(template(this.item.attributes));
        return this;
    }
});

}());
