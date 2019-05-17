#!/usr/bin/env python
# -*- coding: utf-8 -*-

from six.moves import urllib
import datetime
#from datetime import datetime
from subprocess import call
import time
import threading
import os
import json
import time
import signal
import sys
import os.path        # For checking whether secrets file exists
import requests       # For doing the web stuff, dummy!
import operator       # allow assigning dictionary values to a variable 15/07/18
import calendar
import psycopg2
from psycopg2.extras import Json
from psycopg2.extras import register_default_json
from psycopg2.extras import RealDictCursor

reload(sys)
sys.setdefaultencoding('utf8')

###############################################################################
# INITIALISATION
###############################################################################

do_upload = True
# Run without uploading, if specified
if '--no-upload' in sys.argv:
    do_upload = False

def get_parameter( parameter, file_path ):
    # Check if secrets file exists
    if not os.path.isfile(file_path):
        print("File %s not found, exiting."%file_path)
        sys.exit(0)

    # Find parameter in file
    with open( file_path ) as f:
        for line in f:
            if line.startswith( parameter ):
                return line.replace(parameter + ":", "").strip()

    # Cannot find parameter, exit
    print(file_path + "  Missing parameter %s "%parameter)
    sys.exit(0)

# Load configuration from config file
config_filepath = "config.txt"
pleroma_hostname = get_parameter("pleroma_hostname", config_filepath) # E.g., pleroma.site
pleroma_db = get_parameter("pleroma_db", config_filepath) # E.g., pleroma_prod
pleroma_db_user = get_parameter("pleroma_db_user", config_filepath) # E.g., pleroma
grafana_db = get_parameter("grafana_db", config_filepath) # E.g., grafana_prod
grafana_db_user = get_parameter("grafana_db_user", config_filepath) # E.g., pleroma

# Postgres connection strings
cstring_grafana = "dbname=" + grafana_db + " user=" + grafana_db_user + " password='' host='localhost' port='5432'"
cstring_pleroma = "dbname=" + pleroma_db + " user=" + pleroma_db_user + " password='' host='localhost' port='5432'"

###############################################################################
# GET THE DATA from instance's API: user count, domain_count and status count
###############################################################################

# Get current timestamp
ts = int(time.time())

res = requests.get('https://' + pleroma_hostname + '/api/v1/instance?')
current_users = res.json()['stats']['user_count']
num_instances = res.json()['stats']['domain_count']
num_status = res.json()['stats']['status_count']

# Toots per user
status_per_usuari = int (num_status / current_users)

################################################################################
# get the federated hosts from Pleroma`s DB users table
################################################################################

try:
      conn = None
      conn = psycopg2.connect(cstring_pleroma)

      cur = conn.cursor()

      # els developers de Pleroma ho fan aixi : SELECT distinct split_part(nickname, '@', 2) FROM users;
      cur.execute("SELECT DISTINCT info FROM (select info->'source_data'->>'id' AS host FROM users WHERE local='f') AS info")

      host_federats = []
      
      for row in cur:
         host_federats.append(row[0]) ## guarda les urls dels hosts en l'array host_federats

      usuaris_fed = len(host_federats)

      url_federades = []
      i = 0
      url_nova = ''
      sep_dreta = '/users'
      sep_esquerra = '(https://'
      
      while i < len(host_federats)-1:

        url_nova = host_federats[i].rpartition(sep_dreta) 
        url_nova = url_nova[0]
        url_nova = url_nova.partition(sep_esquerra)
        #print url_nova[0]
        url_federades.append(url_nova[2])
        #print host_federats[i]+'>'+url_nova[2]        
       
        i += 1
      
      url_federades = sorted(set(url_federades))
      #print url_federades
      #num_instances = len(url_federades)-1

      cur.close()

except (Exception, psycopg2.DatabaseError) as error:
      print (error)
finally:
      if conn is not None:
        conn.close()

#####################################################################################################
# get unreachable hosts from Pleroma DB table instances                                             #
#  id |     host     |     unreachable_since	  |        inserted_at         |         updated_at #
#####################################################################################################

ara = datetime.datetime.now()
try:
      conn = None
      conn = psycopg2.connect(cstring_pleroma)

      cur = conn.cursor()

      cur.execute("select host, unreachable_since, inserted_at from instances where unreachable_since IS NOT NULL;")

      #row = cur.fetchone()
      #unreachable_hosts = row[0]

      hosts_unreached = []
      hosts_unreached_since = []
      elapsed_days = []
      inserted = []

      for row in cur:
         hosts_unreached.append(row[0]) ## guarda els hosts en l'array hosts_unreached[]
         hosts_unreached_since.append(str(row[1])) ## guarda el timestamp des de quan és unreachable
         elapsed_days.append(ara-row[1])
         inserted.append(str(row[2]))

      unreachable_hosts = len(hosts_unreached)

      cur.close()

except (Exception, psycopg2.DatabaseError) as error:
      print (error)
finally:
      if conn is not None:
        conn.close()

##########################################################################################
# store unreachable hosts data to grafana DB, table servidors_no_responen
#  columns servidor | des_de | dies_sense_resposta | datetime
#########################################################################################

inserta_linia = """INSERT INTO servidors_no_responen(servidor, des_de, dies_sense_resposta, inserted_at)
             VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING;"""
conn = None

i = 0

while i < (len(hosts_unreached)):

  try:

    conn = psycopg2.connect(cstring_grafana)

    cur = conn.cursor()

    # execute INSERT servidor, des_de, dies_sense_resposta, inserted_at, datetime
    cur.execute(inserta_linia, (hosts_unreached[i], hosts_unreached_since[i], elapsed_days[i], inserted[i]))
    # execute UPDATE
    cur.execute("UPDATE servidors_no_responen SET dies_sense_resposta=(%s) where servidor=(%s)", (elapsed_days[i], hosts_unreached[i]))
    cur.execute("UPDATE servidors_no_responen SET datetime=(%s) where servidor=(%s)", (ara, hosts_unreached[i]))    
    
    # delete back on life servers
    cur.execute("DELETE from servidors_no_responen where datetime <> %s", (ara,))
    
    # commit data
    conn.commit()
    # close the connection
    cur.close()

    i = i+1

  except (Exception, psycopg2.DatabaseError) as error:
    print (error)
  finally:
    if conn is not None:
      conn.close()

#################################################################################
# definition of intial values for the very first time running
#################################################################################

usuaris_abans = current_users
toots_abans = num_status
instancies_abans = num_instances
usuarishora = 0
tootshora = 0
instancieshora = 0
actius = 0
actius30= 0
toots_actius = 0
interaccions = 0

usuaris_fed_abans = usuaris_fed

#################################################################################
# Connect to Grafana's Postgresql DB to check if is empty (0 rows)
#################################################################################

try:
  conn = None
  conn = psycopg2.connect(cstring_grafana)

  cur = conn.cursor()

  cur.execute("SELECT * from grafana")
  row = cur.fetchone()
   
  if row > 0:

    ########################################################################################################
    # Connect to Grafana's Postgresql DB to fetch last row local users, toots, instances and federated users
    ########################################################################################################

    try:
      conn = None
      conn = psycopg2.connect(cstring_grafana)

      cur = conn.cursor()

      cur.execute("SELECT DISTINCT ON (datetime) usuaris,toots,instancies,usuaris_federats,datetime FROM grafana WHERE datetime > current_timestamp - INTERVAL '70 minutes' ORDER BY datetime asc LIMIT 1")

      row = cur.fetchone()
      
      if row == None:
        usuaris_abans = current_users
        toots_abans = num_status
        instances_abans = num_instances
        usuaris_fed_abans = usuaris_fed
      else:
        usuaris_abans = row[0]
        toots_abans = row[1]
        instancies_abans = row[2]
        usuaris_fed_abans = row[3]

      # how many statuses at the very beginning of the current week
      cur.execute("SELECT DISTINCT ON (datetime) toots, datetime FROM grafana WHERE datetime > date_trunc('week', now()::timestamp) ORDER by datetime asc LIMIT 1")
  
      row = cur.fetchone()
      
      if row == None:
        toots_inici_setmana = num_status
      else:
        toots_inici_setmana = row[0]
  
      cur.close()
  
      usuarishora = current_users - usuaris_abans
      tootshora = num_status - toots_abans
      instancieshora = num_instances - instancies_abans
      usuarisfedhora = usuaris_fed - usuaris_fed_abans

    except (Exception, psycopg2.DatabaseError) as error:
      print (error)
    finally:
      if conn is not None:
        conn.close()

    #toots_actius = (num_status-toots_inici_setmana)/actius

    print "-----------------"
    print "Current users: "+str(current_users)
    print "Users before: "+str(usuaris_abans)
    print "New users x hour: "+str(usuarishora)
    print "-----------------"
    print "Federated users: "+str(usuaris_fed)
    print "Fed users before: "+str(usuaris_fed_abans)
    print "New fed users: "+str(usuarisfedhora)
    print "-----------------"
    print "Posts: "+str(num_status)
    print "Posts before: "+str(toots_abans)
    print "Posts x hour: "+str(tootshora)
    print("Posts per user: %s "% status_per_usuari)
    print "Posts at beginning current week:"+str(toots_inici_setmana)
    print "-----------------"
    print "Federated servers: "+str(num_instances)
    print "Federated servers before: "+str(instancies_abans)
    print "Federating servers x hour: "+str(instancieshora)
    print "-----------------"
    print "Unreached servers: " + str(len(hosts_unreached))
    print "-----------------"
    #print "Posts this week:"+str(num_status-toots_inici_setmana)
    #print "Active users:"+str(actius)
    #print "Posts x active users: "+str(toots_actius)
  else:
    cur.close()

except (Exception, psycopg2.DatabaseError) as error:
  
  print (error)

finally:
  
  if conn is not None:
      conn.close()

#################################################################################################################################################################################################
# Connect to Grafana's Postgresql DB pleroma_grafana to save all data needed to graph stats
# used columns:                     
# datetime | usuaris | usuarishora | toots | tootshora | tootsusuari | interaccions | actius | actius30 | instancies | instancies hora | tootsactius | usuaris_federats | usuaris_federats_x_hora 
#----------+---------+-------------+-------+-------------+--------------+--------+-----------+----------+------------+---------------------------------------------------------------------------

#def inserta_linia(usuaris):

inserta_linia = """INSERT INTO grafana(datetime, usuaris, usuarishora, toots, tootshora, tootsusuari, interaccions, actius, actius30, instancies, instancieshora, tootsactius, usuaris_federats, usuaris_federats_x_hora)
             VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING datetime;"""
conn = None
    
ara = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

try:
  conn = psycopg2.connect(cstring_grafana)
  
  cur = conn.cursor()
  # execute INSERT 
  ##cur.execute(inserta_linia, (ara, current_users, usuarishora, num_status, tootshora, status_per_usuari, interaccions, actius, actius30, num_instances, instancieshora, toots_actius, usuaris_fed, usuarisfedhora))
  # get the id
  datetime = cur.fetchone()[0]
  # commit data
  conn.commit()
  # close the connection
  cur.close()

except (Exception, psycopg2.DatabaseError) as error:
  print(error)

finally:
  if conn is not None:
    conn.close()
 
###############################################################################
# WORK OUT THE TOOT TEXT
###############################################################################

# Calculate difference in times
hourly_change_string = ""
daily_change_string  = ""
weekly_change_string = ""

#######################################################################################################################
# Connect to Postgresql DB to fetch users increase in the last hour, last day and last week
########################################################################################################################

try:
  conn = None
  conn = psycopg2.connect(cstring_grafana)

  cur = conn.cursor()

  cur.execute("SELECT DISTINCT ON (datetime) usuaris,datetime FROM grafana WHERE datetime > current_timestamp - INTERVAL '70 minutes' ORDER BY datetime asc LIMIT 1")
  
  row = cur.fetchone()
  usuaris_hora = row[0]
  
  cur.execute("SELECT DISTINCT ON (datetime) usuaris,datetime FROM grafana WHERE datetime > current_timestamp - INTERVAL '25 hours' ORDER BY datetime asc LIMIT 1")
  
  row = cur.fetchone()
  usuaris_dia = row[0]

  cur.execute("SELECT DISTINCT ON (datetime) usuaris,datetime FROM grafana WHERE datetime > current_timestamp - INTERVAL '169 hours' ORDER BY datetime asc LIMIT 1")
  
  row = cur.fetchone()
  usuaris_setmana = row[0]

  cur.close()
  
except (Exception, psycopg2.DatabaseError) as error:
  print (error)
finally:
  if conn is not None:
      conn.close()

#########################################################################################################

inc_hora = current_users - usuaris_hora
inc_dia = current_users - usuaris_dia
inc_setmana = current_users - usuaris_setmana

print "New users last hour: "+str(inc_hora)
print "New users last day: "+str(inc_dia)
print "New users last week: "+str(inc_setmana)
print "-----------------"
print "   spla @ 2019   "
print "-----------------"

###################################################################################

# Hourly change
if inc_hora <> 0:

  users_hourly_change = current_users - usuaris_hora
  print "Evolució horaria usuaris: %s"%users_hourly_change
  if users_hourly_change > 0:
    hourly_change_string = "+" + format(users_hourly_change, ",d") + " last hour\n"

    # Daily change
    if inc_dia <> 0:

      daily_change = current_users - usuaris_dia
      print "Evolució diaria: %s"%daily_change
      if daily_change > 0:
        daily_change_string = "+" + format(daily_change, ",d") + " last day\n"

    # Weekly change
    if inc_setmana <> 0:

      weekly_change = current_users - usuaris_setmana
      print "Evolució setmanal: %s"%weekly_change
      if weekly_change > 0:
        weekly_change_string = "+" + format(weekly_change, ",d") + " last week\n"

###############################################################################
# CREATE AND UPLOAD THE CHART
###############################################################################

# Generate chart
##call(["gnuplot", "generate.gnuplot"])


if do_upload:
    # Upload chart
    ##file_to_upload = 'graph.png'

    ##print "Uploading %s..."%file_to_upload
    ##media_dict = mastodon.media_post(file_to_upload,"image/png")

    ##print "Uploaded file, returned:"
    ##print str(media_dict)

    ###############################################################################
    # T  O  O  T !
    ###############################################################################

    if inc_hora <> 0: # toot only if user count is different that last hour 
      toot_text = "We are " + str(current_users) + " users\n"
      toot_text += hourly_change_string
      #if inc_hora > 0:
       # toot_text += pleroma_hostname + "welcomes new users:" + "\n"
        #toot_text += cadena_nous
        #toot_text += "\n"
      toot_text += daily_change_string
      toot_text += weekly_change_string
      toot_text += "Statuses: %s "% num_status + "\n"
      toot_text += "Statuses x user: %s "% toots_per_usuari + "\n"
      toot_text += "\n"
      toot_text += "Week activity" + "\n"
      toot_text += "Interactions: %s "% interaccions + "\n"
      toot_text += "Active users: %s "% actius + "\n"
      toot_text += "\n"
      toot_text += "Connected instances: %s "% num_instances + "\n"
      toot_text += "\n"

      print "Tooting..."
      print toot_text

      #mastodon.status_post(toot_text, in_reply_to_id=None, )

      print "Toot succesful!"
else:
    print("--no-upload specified, so not uploading anything")
