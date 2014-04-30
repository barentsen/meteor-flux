Installation
============

The following steps will make an Ubuntu system ready to run fluxviewer:

Install Python dependencies:
```
conda install psycopg2
```

Install and configure PostgreSQL:
```
sudo apt-get install postgresql postgresql-contrib
vim /etc/postgresql/xxx/pg_hba.conf  # setup access
psql -U postgres -c 'CREATE DATABASE fluxdb;'
psql -U postgres -c 'CREATE DATABASE testdb;'
```