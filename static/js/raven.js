App = Ember.Application.create();

App.store = DS.Store.create({
    revision: 12,
    adapter: DS.DjangoTastypieAdapter.extend({
      namespace: 'api/0.9'
    })
});

App.Feed = DS.Model.extend({
    title: DS.attr('string'),
    link: DS.attr('string'),
    description: DS.attr('string'),
    items: DS.hasMany('App.FeedItem'),
    repr: function() {
        return this.get('title') || this.get('link');
    }.property()
});

App.Item = DS.Model.extend({
    title: DS.attr('string'),
    description: DS.attr('string'),
    feed: DS.belongsTo('App.Feed'),
    published: DS.attr('string')
});

App.Router.map(function() {
    this.resource('account');
    this.resource('help');
});

App.ApplicationRoute = Ember.Route.extend({
    events: {
        addFeed: function(url) {
            var urlregex = new RegExp(
                "^(http:\/\/|https:\/\/|ftp:\/\/){1}([0-9A-Za-z]+\.)");
            if (urlregex.test(url)) {
                var feed = App.Feed.createRecord({
                    link: url
                });
            } else {
                // TODO: handle the error
                console.log('not a url');
            }
        }
    },
    setupController: function(controller) {
    }
});

App.IndexRoute = Ember.Route.extend({
    setupController: function(controller) {
        controller.set('feeds', App.Feed.find());
        controller.set('feeditems', App.Item.find());
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
