DEPLOY CHECKLIST
================
	http://goo.gl/2pki7

The way to publish static assets:
	s3cmd ls
	s3cmd sync static s3://readraven
	go to AWS dashboard and ensure everything is made public


Local Setup
===========
Ensure you have the heroku toolbelt installed:
	https://toolbelt.heroku.com/

Some quick commands are:
  - heroku login
  - heroku ps		# see status of the remote heroku
  - heroku config	# see environment variables in remote heroku

A DANGEROUS command is:
  - heroku pg:reset DATABASE_URL	# this, verbatim, will drop the remotedb

A useful command is:
  - heroku run python manage.py help

Above is a useful quick way to test after a deploy to ensure all the
environment variables are correct, and models validate.


Iterating with Staging
======================
In the early days of readraven, we will use staging quite a bit to test
our setup before pushing to production. Here are some tips on how to do
iterative testing with the remote staging environment.

First, heroku is 'deploy via git'. Not only must everything be checked
in to deploy properly, NOTE that heroku *only* reacts to the 'master'
branch. This can be quite annoying.

To minimize chance of disaster, and to make pushing our iteration
changes easier, let us please standardize on the following workflow.

  1. Assume all development work happens in readraven/
  2. Create a new physical directory named heroku-staging/
  3. Create a new physical directory named heroku-production/

You are free to treat (1) however you like, mixing the AmeliaKnows repo
with your own github repo as various origins.

For (2), you *must* set that to your personal github repo 'master'

For (3), you *must* set to the AmeliaKnows 'master'

For (2) and (3), you must not add any extra remote branches, unless
specified below. This will save us costly mistakes in the future.

Let us now setup directory (2). Substitute your own repo as needed.

    git clone git@github.com:achiang/readraven.git heroku-staging
    cd heroku-staging
    git remote add amelia git@github.com:AmeliaKnows/readraven.git
    git remote update
    git rebase amelia/master

The above will set the master branch of your own repo to equal whatever
is in amelia.

Next, add the following to your .git/config:

    [remote "staging"]
        url = git@heroku.com:readraven-staging.git
        fetch = +refs/heads/*:refs/remotes/staging/*

And finally, again issue:

    git remote update

Now your heroku-staging/ directory points to your own repo as the
special 'origin' branch, and has two remotes: 'amelia' and 'staging'.

stacked git
===========
This is the best tool for working with git. It combines the concepts of
quilt and git into a new kind of awesome.

The problem it solves is: as you are working on a series of changes in
your git branch, after you commit something and are working on the next
commit, you may discover you missed something in a prior commit. The git
data model makes it hard to go back and edit an old commit.

Enter stg. With stg, you still work on a series of patches, but now you
can manage them as a stack, and navigate the stack making changes if
needed. An example:

    git branch foo
    git checkout foo
    stg init
    stg new first-feature
    # Write the changelog for what first-feature might be
    
    # <hack hack hack until satisfied>
    
    stg refresh
    git show		# should show results of hacking as a git commit
    stg new next-feature
    # Write the changelog for next-feature
    
    # <hack hack hack>
    # <realize you forgot something in first-feature>
    
    git diff		# shows dirty status of your tree
    stg refresh		# commits all dirty stuff into 'next-feature'
    stg pop		# go back to 'first-feature'
    # <hack hack hack>
    stg refresh
    git show		# now see how the commit was updated

    stg push		# resume working on 'next-feature'
    stg edit		# update changelog of 'next-feature'

There are lots more commands, but the above captures the essence why stg
is awesome.

It is particularly suited for iterating with heroku, because everything
needs to be committed to 'master' for heroku to use it. If you are
making a bunch of little tests, you will end up with 20 commits on top
of master, with some temporary hacks, little experiments that did not pan
out, etc. Extracting out what you want from those 20 commits into
something you can send a final pull request for can be tedious.

Here is how I do it:

    git branch		# verify I am on 'master'
    git push staging	# push master to heroku staging

    # test in the cloud, notice something is not working

    stg init		# initialize 'master' as an stg branch

    # <hack hack hack>

    stg new fix-name	# git tree is still dirty at this point, no prob!
    # edit fix-name commit log

    stg refresh		# now you have a new commit in master
    git push staging	# test in heroku again, notice it *still* not working

    # <hack hack hack>
    stg refresh		# the same commit in master was updated

    git push --force staging	# push again to heroku

    <repeat as necessary; create a new stg patch for each new logical change>

    stg publish my-branch	# creates a new local git branch my-branch
    git checkout my-branch
    git log			# verify log has the commits from your
    				# iteration cycle

    git push origin my-branch	# push branch to achiang/readraven.git

    # Send pull request via github


Staging
=======
A staging heroku app has been created using instructions from [1].

	$ heroku create --remote staging
	$ git push staging master


Its url is:
	http://readraven-staging.herokuapp.com/

To get it to work properly, all the environment variables
must be set:

	heroku config:set SECRET_KEY=...
	heroku config:set STRIPE_PUBLIC_KEY=...
	heroku config:set STRIPE_SECRET_KEY=...
	heroku config:set DJANGO_SETTINGS_MODULE=raven.settings.staging
	heroku config:set HTTPS=on

Also note that the settings in raven/settings/staging.py is quite
important here. Especially note that the database we use there is
different from the production database.

Production
==========
A production heroku app has also been created, but as of this writing,
nothing is really there yet. I expect the only real difference will be
setting the DJANGO_SETTINGS_MODULE=raven.settings.production, but of
course, we shall see.


Addons we use
=============
    heroku addons:add heroku-postgresql:dev
    heroku addons:add cloudamqp


References
==========
1: https://devcenter.heroku.com/articles/multiple-environments
2: https://devcenter.heroku.com/articles/config-vars
