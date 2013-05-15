(function() {
"use strict";
window.APP = window.APP || {Routers: {}, Collections: {}, Models: {}, Views: {}};
Backbone.Tastypie.doGetOnEmptyPostResponse = true;
Backbone.Tastypie.doGetOnEmptyPutResponse = true;

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

}());
