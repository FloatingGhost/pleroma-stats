Graphical Pleroma's stats with Python + Postgresql+ Grafana
===========================================================

Python script that gets stats data from [Pleroma](https://pleroma.social) API.

### Dependencies

-   **Python 2**
-   Grafana server
-   Postgresql server 
-   Everything else at the top of `pleroma-stats.py`!

### Usage:

1. Edit `config.txt` to specify the hostname of the Pleroma server you would like to get data from, its DB 
   name and user and the DB name and user to use from Grafana.

2. Create one Postgresql database for Grafana, in example 'pleroma-stats', with two tables:

CREATE TABLE stats(
DATETIME TIMESTAMPTZ PRIMARY KEY NOT NULL,
USERS INT,
USERS_HOUR INT,
POSTS INT,
POSTS_HOUR INT, POSTS_USERS INT,
INTERACTIONS INT,
ACTIVE INT, ACTIVE30 INT,
SERVERS INT, SERVERS_HOUR INT,
POSTS_ACTIVE INT,
FEDERATED_USERS INT, FEDERATED_USERS_HOUR INT
);

CREATE TABLE unreached_servers(
SERVER VARCHAR(30),
SINCE TIMESTAMP,
DAYS VARCHAR(30),
INSERTED_AT TIMESTAMP PRIMARY KEY NOT NULL,
DATETIME TIMESTAMPTZ
);

3. Use your favourite scheduling method to set `./pleroma-stats.py` to run regularly.

Then you could graph your Pleroma server stats with Grafana's PostgreSQL datasource!
It gets all needed data from Pleroma server API and Postgresql database and then store all stats to a new Postgresql database created above.

