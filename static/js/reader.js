(function() {
"use strict";
window.APP = window.APP || {Routers: {}, Collections: {}, Models: {}, Views: {}};

APP.Routers.ReaderRouter = Backbone.Router.extend({
    routes: {
        '/': 'index'
    },
    initialize: function(options) {
        this.feeds = new APP.Collections.Feeds();
        this.items = new APP.Collections.FeedItems();
        this.feeds.fetch().then(_.bind(function(args) {
            this.items.fetch().then(_.bind(function(args) {
                this.index();
            }, this));
        }, this));
    },
    index: function() {
        this.currentView = new APP.Views.Reader({
            feeds: this.feeds,
            items: this.items
        });
        $('#main').html(this.currentView.render().el);
    }
});

var router = new APP.Routers.ReaderRouter({});
Backbone.history.start();

}());
