(function() {
"use strict";
window.APP=window.APP||{Routers:{},Collections:{},Models:{},Views:{}};

/*
 * This is recommended by backbone-tastypie. I'm suspicious that it might be
 * overly talkative on the wire, so I'm disabling it for now.
Backbone.Tastypie.doGetOnEmptyPostResponse = true;
Backbone.Tastypie.doGetOnEmptyPutResponse = true;
 */

var Models = APP.Models.Item = Backbone.Model.extend({
    urlRoot: '/api/0.9.5/item/'
});
APP.Collections.Items = Backbone.Collection.extend({
    defaultParams: {
        read: false,
        order_by: '-published'
    },
    model: Models,
    params: {},
    url: function() {
        var params = _.defaults(this.params, this.defaultParams);
        return '/api/0.9.5/item/?' + $.param(params);
    }
});

}());
