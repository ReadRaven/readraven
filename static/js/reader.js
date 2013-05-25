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
        this.readerView = new APP.Views.Reader();
    },
    reader: function() {
        this.readerView.setFeed();
        this.readerView.render();
    },
    feed: function(id) {
        this.readerView.setFeed(id);
        this.readerView.render();
    }
});

var router = new APP.Routers.ReaderRouter();
Backbone.history.start();

}());
