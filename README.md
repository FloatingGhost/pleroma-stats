Graphical Pleroma's stats with Python + Postgresql+ Grafana
===========================================================

Python script that gets stats data from Pleroma API [Mastodon](https://github.com/tootsuite/mastodon).

### Dependencies

-   **Python 2**
-   [Mastodon.py](https://github.com/halcy/Mastodon.py): `pip install Mastodon.py`
-   Everything else at the top of `usercount.py`!
-   If you want Postgresql version use `usercount-postgresql.py`!

### Usage:

1. Edit `config.txt` to specify the hostname of the Pleroma instance you would like to get data from, its DB 
   name and user and the DB name and user to use with Grafana.
2. Create a file called `secrets.txt` in the folder `secrets/`, as follows:

```
uc_client_id: <your client ID>
uc_client_secret: <your client secret>
uc_access_token: <your access token>
```

3. Use your favourite scheduling method to set `./usercount.py` to run regularly.
4. Or use your favourite scheduling method to set `./usercount-postgresql.py` to run regularly if you prefer the Postgresql version. To do so, you need to create a Postgresql database named 'pggrafana' and then create 'grafana' table like this:

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

Then you could graph your Mastodon instance stats with Grafana's PostgreSQL datasource!
The usercount-postgresql.py script do not use csv files at all. 
It gets all needed data from Mastodon instance API and Postgresql database and then store all stats to a new Postgresql database created above.

Call the script you choose from point 3 or 4 with the `--no-upload` argument if you don't want to upload anything.

Note: The script will fail to output a graph until you've collected data points that are actually different!
