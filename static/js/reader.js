(function() {
"use strict";
window.APP = window.APP || {Routers: {}, Collections: {}, Models: {}, Views: {}};

APP.Routers.ReaderRouter = Backbone.Router.extend({
    routes: {
        'feed/:id': 'feed',
        '*default': 'reader'
    },
    initializer: function(config) {
        this.feeds = this.feeds || new APP.Collections.Feeds();
        // TODO: fetch all feeds if they haven't been previously fetched.
    },
    reader: function() {
        var feeds = this.feeds || new APP.Collections.Feeds();
        var items = new APP.Collections.FeedItems();
        feeds.fetch().then(_.bind(function(args) {
            if (this.feeds == undefined) {
                this.feeds = feeds;
            }
            items.fetch().then(_.bind(function(args) {
                this.currentView = new APP.Views.Reader({
                    feeds: feeds,
                    items: items
                });
                this.currentView.render();
            }, this));
        }, this));
    },
    feed: function(id) {
        var feeds = this.feeds || new APP.Collections.Feeds();
        feeds.fetch().then(_.bind(function(args) {
            if (this.feeds == undefined) {
                this.feeds = feeds;
            }
            var feed = feeds.where({id: parseInt(id, 10)})[0];
            var items = new APP.Collections.FeedItems(feed.get('items'));
            items.fetch().then(_.bind(function(args) {
                this.currentView = new APP.Views.Reader({
                    feed: feed,
                    feeds: feeds,
                    items: feed.get('items')
                });
                this.currentView.render();
            }, this));
        }, this));
    }
});

var router = new APP.Routers.ReaderRouter({});
Backbone.history.start();

}());
