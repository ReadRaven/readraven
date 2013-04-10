App = Ember.Application.create();

App.User = Ember.Object.extend({
    fullName: '',
    email: '',
});

App.Post = Ember.Object.extend({
    title: '',
    description: '',
    published: ''
});

App.Router.map(function() {
    this.resource('account');
    this.resource('help');
});

App.ApplicationRoute = Ember.Route.extend({
    model: function() {
        return App.User.create({
            email: 'paul@eventuallyanyway.com'
        });
    }
});

App.IndexRoute = Ember.Route.extend({
    model: function() {
        return [{
            title: 'Title 1',
            description: 'This is the description for the first post.'
        }, {
            title: 'Post Numbah 2',
            description: 'The second post has a different description'
        }];
    }
});
