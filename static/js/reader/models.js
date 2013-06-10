(function() {
"use strict";
window.APP=window.APP||{Routers:{},Collections:{},Models:{},Views:{}};

/*
 * This is recommended by backbone-tastypie. I'm suspicious that it might be
 * overly talkative on the wire, so I'm disabling it for now.
Backbone.Tastypie.doGetOnEmptyPostResponse = true;
Backbone.Tastypie.doGetOnEmptyPutResponse = true;
 */

var Feed = APP.Models.Feed = Backbone.Model.extend({
    urlRoot: '/api/0.9.5/feed/'
});

var Item = APP.Models.Item = Backbone.Model.extend({
    urlRoot: '/api/0.9.5/item/'
});
APP.Collections.Items = Backbone.Collection.extend({
    defaultParams: {
        read: false,
        order_by: '-published'
    },
    getNext: function() {
        if (this.length == this._total) {
            /* We have all the feeds. */
            console.log('All feeds already fetched.');
            return -1;
        }
        this.fetch({add: true, success: this.onSuccess});
    },
    hasNext: function() {
        return (this.length !== this._total);
    },
    model: Item,
    params: {},
    success: function(self, res, options) {
        if (self.total != res.meta.total_count) {
            self.total = res.meta.total_count;
        }
        if (self.params.limit != res.meta.limit) {
            self.params.limit = res.meta.limit;
        }
        self.params.offset = res.meta.offset+self.params.limit;
    },
    total: 0,
    url: function() {
        var params = _.defaults(this.params, this.defaultParams);
        var url = '/api/0.9.5/item/?' + $.param(params);
        return url;
    }
});

}());
