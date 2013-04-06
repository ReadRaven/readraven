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
