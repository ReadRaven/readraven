App = Ember.Application.create();

DS.RESTAdapter.reopen({
    namespace: 'api/0.9'
});

App.Store = DS.Store.extend({
    revision: 12,
    adapter: 'DS.FixtureAdapter'
});

App.User = DS.Model.extend({
    fullName: DS.attr('string'),
    email: DS.attr('string')
});

App.User.FIXTURES = [
    {id: 1, email: 'paul@eventuallyanyway.com', fullName: 'Paul Hummer'}
];

App.Feed = DS.Model.extend({
    title: DS.attr('string'),
    link: DS.attr('string'),
    description: DS.attr('string'),
    items: DS.hasMany('App.FeedItem'),
    repr: function() {
        return this.get('title') || this.get('link');
    }.property()
});

App.Feed.FIXTURES = [
    {id: 1, title: 'Super Feed', description: 'The best feed'},
    {id: 2, title: 'Worst Feed', description: 'A terrible feed'},
    {id: 3, title: 'Mediocre Feed', description: 'Feed. Meh.'},
    {id: 4, title: 'Weird Feed', description: 'Feeds is weird'},
    {id: 5, title: 'Awkward Feed', description: 'An awkward feed'},
];

App.FeedItem = DS.Model.extend({
    title: DS.attr('string'),
    description: DS.attr('string'),
    feed: DS.belongsTo('App.Feed'),
    published: DS.attr('string')
});

App.FeedItem.FIXTURES = [{
    id: 1,
    title: 'Super amazing post',
    description: 'There are no better feeds than this one',
    feed: 1
}, {
    id: 2,
    title: 'Super amazing post 2',
    description: 'Things are getting better',
    feed: 1
}, {
    id: 3,
    title: 'Super amazing post 3',
    description: 'Okay. <i>This</i> is the pinnacle of feeds.',
    feed: 1
}, {
    id: 4,
    title: 'Super amazing post',
    description: 'There are no better feeds than this one',
    feed: 5
}];

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
        var user = App.User.find(1);
        controller.set('user', user);
    }
});

App.IndexRoute = Ember.Route.extend({
    setupController: function(controller) {
        controller.set('feeds', App.Feed.find());
        controller.set('feeditems', App.FeedItem.find());
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
