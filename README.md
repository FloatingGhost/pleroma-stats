Graphical Pleroma's stats with Python + Postgresql+ Grafana
===========================================================

Python script that gets stats data from [Pleroma](https://pleroma.social) API.

### Dependencies

-   **Python 2**
-   Everything else at the top of `pleroma-stats.py`!

### Usage:

1. Edit `config.txt` to specify the hostname of the Pleroma instance you would like to get data from, its DB 
   name and user and the DB name and user to use with Grafana.

2. Create one Postgresql database with two tables:

CREATE TABLE grafana(
DATETIME TIMESTAMPTZ PRIMARY KEY NOT NULL,
USUARIS INT,
USUARISHORA INT,
TOOTS INT,
TOOTSHORA INT, TOOTSUSUARI INT,
INTERACCIONS INT,
ACTIUS INT, ACTIUS30 INT,
INSTANCIES INT, INSTANCIESHORA INT,
TOOTSACTIUS INT
);

3. Use your favourite scheduling method to set `./pleroma-stats.py` to run regularly.

Then you could graph your Pleroma server stats with Grafana's PostgreSQL datasource!
It gets all needed data from Pleroma server API and Postgresql database and then store all stats to a new Postgresql database created above.

