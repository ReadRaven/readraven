(function() {
"use strict";
window.APP = window.APP || {Routers: {}, Collections: {}, Models: {}, Views: {}};

Handlebars.registerHelper('formatDate', function(context, block) {
    //var f = block.hash.format || "MMM Do, YYYY";
    return moment(context).fromNow();
});

APP.Routers.ReaderRouter = Backbone.Router.extend({
    routes: {
        'feed/:id': 'feed',
        '*default': 'reader'
    },
    initialize: function(config) {
        this.feeds = new APP.Collections.Feeds();
    },
    reader: function() {
        var items = new APP.Collections.FeedItems();

        this.currentView = new APP.Views.Reader({
            feeds: this.feeds,
            items: items
        });
        this.currentView.render();
    },
    feed: function(id) {
        this.currentView = new APP.Views.Reader({
            feedID: id,
            feeds: this.feeds,
        });
        this.currentView.render();
    }
});

var router = new APP.Routers.ReaderRouter();
Backbone.history.start();

}());
