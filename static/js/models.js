(function() {
"use strict";
window.APP = window.APP || {Routers: {}, Collections: {}, Models: {}, Views: {}};
Backbone.Tastypie.doGetOnEmptyPostResponse = true;
Backbone.Tastypie.doGetOnEmptyPutResponse = true;

APP.Models.Feed = Backbone.RelationalModel.extend({
    relations: [{
        type: Backbone.HasMany,
        key: 'items',
        relatedModel: 'APP.Models.FeedItem',
        collectionType: 'APP.Collections.FeedItems',
        reverseRelation: {
            key: 'feed',
            includeInJSON: 'resource_uri'
        }
    }],
    urlRoot: '/api/0.9/feed/'
});
APP.Collections.Feeds = Backbone.Collection.extend({
    model: APP.Models.Feed,
    url: '/api/0.9/feed/'
});
APP.Models.FeedItem = Backbone.RelationalModel.extend({
    urlRoot: '/api/0.9/item/'
});
APP.Collections.FeedItems = Backbone.Collection.extend({
    model: APP.Models.FeedItem,
    url: '/api/0.9/item/'
});

}());
