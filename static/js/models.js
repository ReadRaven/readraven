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
    onSuccess: function(collection, response, options) {
        if (response.meta.next !== null) {
            var limit = response.meta.limit,
                offset = response.meta.offset,
                params = {
                    data: {
                        limit: limit,
                        offset: offset+limit
                    },
                    success: collection.onSuccess
                };
            collection.fetch(params);
        }
    },
    model: APP.Models.Feed,
    url: '/api/0.9/feed/'
});
APP.Models.FeedItem = Backbone.RelationalModel.extend({
    urlRoot: '/api/0.9/item/'
});
APP.Collections.FeedItems = Backbone.Collection.extend({
    _limit: 0,
    _offset: 0,
    _total: 0,
    onSuccess: function(collection, response, options) {
        if (collection._total != response.meta.total_count) {
            collection._total = response.meta.total_count;
        }
        if (collection._limit != response.meta.limit) {
            collection._limit = response.meta.limit;
        }
        collection._offset = response.meta.offset;
        /* If you want to see this in action (and LMFAO), uncomment this line.
        collection.getNext();
         */
    },
    getNext: function() {
        if (this.length == this._total) {
            return -1; // We have all the feeds.
        }

        var params = {
                data: {
                    limit: this._limit,
                    offset: this._offset+this._limit
                },
                success: this.onSuccess
            };
        this.fetch(params);
    },
    model: APP.Models.FeedItem,
    url: '/api/0.9/item/'
});

}());
