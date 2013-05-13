(function() {
"use strict";
window.APP = window.APP || {Routers: {}, Collections: {}, Models: {}, Views: {}};
Backbone.Tastypie.doGetOnEmptyPostResponse = true;
Backbone.Tastypie.doGetOnEmptyPutResponse = true;

APP.Routers.ReaderRouter = Backbone.Router.extend({
    routes: {
        '/': 'index'
    },
    initialize: function(options) {
        this.feeds = new APP.Collections.Feeds();
        this.feeds.fetch().then(_.bind(function(args) {
            this.index();
        }, this));
    },
    index: function() {
        this.currentView = new APP.Views.FeedListView({feeds: this.feeds});
        $('#main').html(this.currentView.render().el);
    }
});

APP.Models.Feed = Backbone.Model.extend({
    defaults: {
        description: '',
        link: '',
        title: '',
        items: []
    },
    urlRoot: '/api/0.9/feed/',
});
APP.Collections.Feeds = Backbone.Collection.extend({
    model: APP.Models.Feed,
    url: '/api/0.9/feed/'
});
APP.Models.FeedItem = Backbone.Model.extend({
    defaults: {
        title: '',
        description: '',
        feed: null,
        link: '',
        read: false
    },
    urlRoot: '/api/0.9/feed/',
});
APP.Collections.FeedItems = Backbone.Collection.extend({
    model: APP.Models.FeedItem,
    url: '/api/0.9/item/'
});

APP.Views.FeedListView = Backbone.View.extend({
    _renderFeeds: function() {
        var el = this.$el.find('#feed-list');
        el.children().remove();
        _.each(this.feeds.models, _.bind(function(feed) {
            var view = new APP.Views.FeedListingView({feed: feed});
            el.append(view.render().el);
        }, this));
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
        this.feeds.bind('add', _.bind(this._renderFeeds, this));
        this.feeds.bind('remove', _.bind(this._renderFeeds, this));
    },
    render: function() {
        var template = Handlebars.compile($('#index-template').html());
        this.$el.html(template);

        this._renderFeeds();
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

var router = new APP.Routers.ReaderRouter({});
Backbone.history.start();

}());
