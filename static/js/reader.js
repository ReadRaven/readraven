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

        this.currentView = new APP.Views.Reader({
            feeds: feeds,
            items: items
        });
        this.currentView.render();
    },
    feed: function(id) {
        var feeds = this.feeds || new APP.Collections.Feeds();

        this.currentView = new APP.Views.Reader({
            feedID: id,
            feeds: feeds,
        });
        this.currentView.render();
    }
});

var router = new APP.Routers.ReaderRouter({});
Backbone.history.start();

}());
