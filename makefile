to_mysql:
	docker exec -it mysql mysql -u"${USER}" -p"${PASSWORD}" ${DATABASE}

to_mysql_root:
	docker exec -it mysql mysql -u"root" -p"${ROOT_PASSWORD}" ${DATABASE}

mysql_create:
	docker exec -it mysql mysql --local_infile -u"${USER}" -p"${PASSWORD}" ${DATABASE} -e"source /tmp/load_dataset/mysql_datasource.sql"

mysql_load:
	docker exec -it mysql mysql --local_infile -u"${USER}" -p"${PASSWORD}" ${DATABASE} -e"source /tmp/load_dataset/mysql_load.sql"

to_postgres:
	docker exec -it postgres psql -U postgres -d goodreads