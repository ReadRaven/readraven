App = Ember.Application.create();


var adapter = DS.DjangoTastypieAdapter.extend({
    namespace: 'api/0.9'
});
adapter.map('App.Item', {
    feed: {embedded: 'load', key: 'feed'}
});
App.store = DS.Store.create({
    revision: 12,
    adapter: adapter
});

App.Feed = DS.Model.extend({
    title: DS.attr('string'),
    link: DS.attr('string'),
    description: DS.attr('string'),
    items: DS.hasMany('App.Item'),
    repr: function() {
        return this.get('title') || this.get('link');
    }.property()
});

App.Item = DS.Model.extend({
    link: DS.attr('string'),
    title: DS.attr('string'),
    description: DS.attr('string'),
    feed: DS.belongsTo('App.Feed'),
    published: DS.attr('string')
});

App.Router.map(function() {
    this.resource('feed', { path: '/feed/:id' });

    this.resource('account');
    this.resource('help');
});

App.ApplicationRoute = Ember.Route.extend({
    setupController: function(controller, model) {
        controller.set('all_feeds', App.Feed.find());
    }
});

App.IndexRoute = Ember.Route.extend({
    events: {
        addFeed: function(url) {
            var urlregex = new RegExp(
                "^(http:\/\/|https:\/\/|ftp:\/\/){1}([0-9A-Za-z]+\.)");
            if (urlregex.test(url)) {
                var feed = App.Feed.createRecord({
                    link: url
                });
                feed.get('transaction').commit()
            } else {
                // TODO: handle the error
                console.log('not a url');
            }
        }
    },
    setupController: function(controller) {
        controller.set('items', App.Item.find());
    }
});

App.FeedRoute = Ember.Route.extend({
    model: function(params) {
        return App.Feed.find(params.id);
    },
    setupController: function(controller, model) {
            debugger;
        if (typeof(model) == "string") {
            controller.set('items', App.Item.find({feed: model}));
        } else {
            controller.set('items', App.Item.find({feed: model.id}));
        }
        //var items = model.get('items');
        //var items = App.Item.find({feed: model});
        //controller.set('items', items);
        //controller.set('items', App.Item.find({feed: model}));
        //controller.set('items', model.get('items'));
    }
});

App.AddFeedView = Ember.View.extend({
    classNames: ['btn'],
    click: function(e) {
        e.preventDefault();
        this.get('controller').send('addFeed', $('#add-feed').val());
        $('#add-feed').val('');
    },
    tagName: 'button',
    template: Ember.Handlebars.compile('Add Feed')
});
