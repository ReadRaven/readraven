(function() {
"use strict";
window.APP=window.APP||{Routers:{},Collections:{},Models:{},Views:{}};

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

APP.Routers.Router = Backbone.Router.extend({
    default: function() {
        if (this.strongSide === undefined) {
            this.strongSide = new APP.Views.StrongSide();
        } else {
            this.strongSide.filter({});
        }
        if (!this.leftSide.rendered) {
            this.leftSide.render();
        }
    },
    feed: function(id) {
        if (this.strongSide === undefined) {
            this.strongSide = new APP.Views.StrongSide({params: {feed: id}});
        } else {
            this.strongSide.filter({feed: id});
        }
        if (!this.leftSide.rendered) {
            this.leftSide.render();
        }
    },
    initialize: function(config) {
        this.leftSide = new APP.Views.LeftSide();
    },
    routes: {
        'feed/:id': 'feed',
        '*default': 'default'
    }
});

var router = new APP.Routers.Router();
Backbone.history.start();
}());
