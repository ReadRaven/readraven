required packages
=================
 * librabbitmq0
 * postgresql
 * libpq-dev


system postgres setup 
=====================
	sudo -u postgres psql template1

Set password; I used postgres

	sudo vi /etc/postgresql/9.1/main/pg_hba.conf

And modify line to read as 'md5' (changed from 'peer')

	# Database administrative login by Unix domain socket
	local   all             postgres                                md5


hook up readraven to postgres
=============================
	createdb readraven
	echo "CREATE USER readraven WITH ENCRYPTED PASSWORD 'readraven';" | psql -U postgres
	echo "ALTER USER readraven WITH CREATEDB CREATEUSER;" | psql -U postgres


south migrations
================
There is a dependency between usher and raven, and we should always
migrate the usher app before migrating the raven app.

        python manage.py schemamigration usher --auto
        python manage.py schemamigration raven --auto
        python manage.py migrate taggit
        python manage.py migrate djcelery
        python manage.py migrate usher
        python manage.py migrate raven


rabbitmq
========
$ sudo apt-get install rabbitmq-server
$ sudo rabbitmqctl add_user readraven readraven
$ sudo rabbitmqctl add_vhost /readraven
$ sudo rabbitmqctl set_permissions -p /readraven readraven ".*" ".*" ".*"
