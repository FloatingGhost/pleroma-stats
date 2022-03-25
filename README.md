# Graphical Pleroma stats with Python + PostgreSQL + Grafana

Python script that gets *realtime* stats data from
[Pleroma](https://pleroma.social)'s DB.

## Dependencies

- Python 3
- Grafana (for visualizations)
- PostgreSQL server

Install python deps:

```bash
sudo python -m pip install psycopg2
```

## Usage

1. Edit `config.txt` to specify the hostname of the Pleroma server you
   would like to get data from, its DB name and DB user and also the DB
   name and DB user for Grafana.
2. Create one Postgresql database for Grafana, in this example,
   'pleroma_stats':

    ```text
    sudo -Hu postgres psql < setup_database.sql
    ```

3. `python pleroma-stats.py`
4. Use your favorite scheduling method to set `pleroma-stats.py` to run
   regularly.
5. Add the data source PostgreSQL to your Grafana, configuring Host
   (usually `localhost:5432`), Database (in the example is
   `pleroma_stats`) and User fields.

Then you could graph your Pleroma server stats with Grafana's PostgreSQL
data source! It gets all needed data from Pleroma's PostgreSQL database
and then store stats to a new PostgreSQL database created above, to feed
Grafana with their values.

## Grafana Dashboard

There's a JSON model of a Grafana dashboard in the `contrib/` directory.
(Feel free to improve it and send a patch!)
