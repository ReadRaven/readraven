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
            /* For some reason, the cookie is only set *sometimes*. NFC.
            var csrftoken = $.cookie('csrftoken');
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
            */
            xhr.setRequestHeader("X-CSRFToken", window.CSRFTOKEN);
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
    account: function() {
        if (!this.leftSide.rendered) {
            this.leftSide.render();
        }
        if (this.feedItemList !== undefined) {
            this.feedItemList.hide();
        }

        if (this.accountManage === undefined) {
            this.accountManage = new APP.Views.AccountManageView();
            this.accountManage.render();
        } else {
            this.accountManage.show();
        }
    },
    all: function() {
        if (!this.leftSide.rendered) {
            this.leftSide.render();
        }
        if (this.accountManage !== undefined) {
            this.accountManage.hide();
        }

        var params = {read: '~~~'};
        if (this.feedItemList === undefined) {
            this.feedItemList = new APP.Views.FeedItemList({params: params});
        } else {
            this.feedItemList.filter(params);
        }
    },
    feed: function(id) {
        if (!this.leftSide.rendered) {
            this.leftSide.render();
        }
        if (this.accountManage !== undefined) {
            this.accountManage.hide();
        }
        if (this.feedItemList === undefined) {
            this.feedItemList = new APP.Views.FeedItemList({params: {feed: id}});
        } else {
            this.feedItemList.filter({feed: id});
        }
    },
    feeds: function() {
        if (!this.leftSide.rendered) {
            this.leftSide.render();
        }
        if (this.accountManage !== undefined) {
            this.accountManage.hide();
        }
        if (this.feedItemList !== undefined) {
            this.feedItemList.hide();
        }
    },
    initialize: function(config) {
        this.leftSide = new APP.Views.LeftSide();
    },
    routes: {
        'account': 'account',
        'all': 'all',
        'feeds': 'feeds',
        'feed/:id': 'feed',
        'shared': 'shared', /* Not yet implemented. */
        'starred': 'starred',
        'tag/:tag': 'tag', /* Not yet implemented. */
        'unread': 'unread',
        '*unread': 'unread'
    },
    shared: function() {
        console.log('shared view');
    },
    starred: function() {
        if (!this.leftSide.rendered) {
            this.leftSide.render();
        }
        if (this.accountManage !== undefined) {
            this.accountManage.hide();
        }
        if (this.feedItemList === undefined) {
            this.feedItemList = new APP.Views.FeedItemList({params: {starred: true}});
        } else {
            this.feedItemList.filter({
                starred: true
            });
        }
    },
    tag: function(tag) {
        console.log('Tag view for tag: '+tag);
    },
    unread: function() {
        if (!this.leftSide.rendered) {
            this.leftSide.render();
        }
        if (this.accountManage !== undefined) {
            this.accountManage.hide();
        }
        if (this.feedItemList === undefined) {
            this.feedItemList = new APP.Views.FeedItemList();
        } else {
            this.feedItemList.filter();
        }
    }
});

var router = new APP.Routers.Router();
Backbone.history.start();
}());
