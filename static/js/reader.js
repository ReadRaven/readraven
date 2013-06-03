(function() {
"use strict";
window.APP = window.APP||{Routers:{},Collections:{},Models:{},Views:{}};

Handlebars.registerHelper('formatDate', function(context, block) {
    //var f = block.hash.format || "MMM Do, YYYY";
    var published = moment.utc(context);

    if (moment.utc().diff(published, 'days') > 0) {
        return published.format('LL');
    } else {
        return published.fromNow();
    }
});

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^(GET|HEAD)$/.test(settings.type))) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            var csrftoken = $.cookie('csrftoken');
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    },
    crossDomain: false
});
$(document).bind('ajaxStart', function() {
    $('.loading').show();
}).bind('ajaxStop', function() {
    $('.loading').hide();
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
