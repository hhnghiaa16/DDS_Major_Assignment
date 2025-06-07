import psycopg2
from pathlib import Path



#user=root || postgres
#password=root || newpassword
def getopenconnection(user="postgres", password="newpassword", port=5001, host="localhost", dbname="postgres"):
    try:
        conn_params = {
        'dbname': dbname,
        'user': user,
        'password': password,
        'host': host,
        'port': port
    }
        # print(f"Connecting to the database {conn_params}")
        conn=psycopg2.connect(**conn_params)
        # print(f"Connected to the database {conn}")
        return conn
    except psycopg2.Error as e:
        print("Error connecting to the database")
        print(e)
        return None

def loadratings(ratingstablename, ratingsfilepath, openconnection): 
   
    con = openconnection
    cur = con.cursor()
    print(f"Loading data from {ratingsfilepath} to {ratingstablename}")
    
    cur.execute("create table " + ratingstablename + "(userid integer, extra1 char, movieid integer, extra2 char, rating float, extra3 char, timestamp bigint);")
    cur.copy_from(open(ratingsfilepath),ratingstablename,sep=':')
    
    cur.execute("alter table " + ratingstablename + " drop column extra1, drop column extra2, drop column extra3, drop column timestamp;")
    cur.execute("SELECT * FROM " + ratingstablename + " LIMIT 5")
    rows = cur.fetchall()
    for row in rows:
        print(f"Row: {row}")
    cur.close()
    con.commit()

def rangepartition(ratingstablename, numberofpartitions, openconnection):
    
    con = openconnection
    cur = con.cursor()
    delta = 5 / numberofpartitions
    print(f"Delta: {delta}")
    RANGE_TABLE_PREFIX = 'range_part'
    for i in range(0, numberofpartitions):
        minRange = i * delta
        maxRange = minRange + delta
        table_name = RANGE_TABLE_PREFIX + str(i)

        cur.execute("create table " + table_name + " (userid integer, movieid integer, rating float);")
        if i == 0:
            cur.execute("insert into " + table_name + " (userid, movieid, rating) select userid, movieid, rating from " + ratingstablename + " where rating >= " + str(minRange) + " and rating <= " + str(maxRange) + ";")
        else:
            cur.execute("insert into " + table_name + " (userid, movieid, rating) select userid, movieid, rating from " + ratingstablename + " where rating > " + str(minRange) + " and rating <= " + str(maxRange) + ";")

       
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cur.fetchone()[0]
        print(f"[DEBUG] Inserted {count} rows into {table_name}")
    cur.close()
    con.commit()

def roundrobinpartition(ratingstablename, numberofpartitions, openconnection):
  
    con = openconnection
    cur = con.cursor()
    RROBIN_TABLE_PREFIX = 'rrobin_part'
    for i in range(0, numberofpartitions):
        table_name = RROBIN_TABLE_PREFIX + str(i)
        cur.execute("create table " + table_name + " (userid integer, movieid integer, rating float);")
        cur.execute("insert into " + table_name + " (userid, movieid, rating) select userid, movieid, rating from (select userid, movieid, rating, ROW_NUMBER() over() as rnum from " + ratingstablename + ") as temp where mod(temp.rnum-1, "+ str(numberofpartitions) + ") = " + str(i) + ";")
    cur.close()
    con.commit()

def roundrobininsert(ratingstablename, userid, itemid, rating, openconnection):
    """
    Function to insert a new row into the main table and specific partition based on round robin
    approach.
    """
    con = openconnection
    cur = con.cursor()
    RROBIN_TABLE_PREFIX = 'rrobin_part'
    cur.execute("insert into " + ratingstablename + "(userid, movieid, rating) values (" + str(userid) + "," + str(itemid) + "," + str(rating) + ");")
    cur.execute("select count(*) from " + ratingstablename + ";")
    total_rows = (cur.fetchall())[0][0]
    numberofpartitions = count_partitions(RROBIN_TABLE_PREFIX, openconnection)
    index = (total_rows-1) % numberofpartitions
    table_name = RROBIN_TABLE_PREFIX + str(index)
    cur.execute("insert into " + table_name + "(userid, movieid, rating) values (" + str(userid) + "," + str(itemid) + "," + str(rating) + ");")
    cur.close()
    con.commit()

def rangeinsert(ratingstablename, userid, itemid, rating, openconnection):
    
    con = openconnection
    cur = con.cursor()
    RANGE_TABLE_PREFIX = 'range_part'
    cur.execute("insert into " + ratingstablename + "(userid, movieid, rating) values (" + str(userid) + "," + str(itemid) + "," + str(rating) + ");")
    numberofpartitions = count_partitions(RANGE_TABLE_PREFIX, openconnection)
    delta = 5 / numberofpartitions
    index = int(rating / delta)
    if rating % delta == 0 and index != 0:
        index = index - 1
    table_name = RANGE_TABLE_PREFIX + str(index)
    cur.execute("insert into " + table_name + "(userid, movieid, rating) values (" + str(userid) + "," + str(itemid) + "," + str(rating) + ");")
    cur.close()
    con.commit()

def create_db(dbname):
    """
    We create a DB by connecting to the default user and database of Postgres
    The function first checks if an existing database exists for a given name, else creates it.
    :return:None
    """
    # Connect to the default database
    con = getopenconnection()
    con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()

    # Check if an existing database with the same name exists
    cur.execute('SELECT COUNT(*) FROM pg_catalog.pg_database WHERE datname=\'%s\'' % (dbname,))
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute('CREATE DATABASE %s' % (dbname,))  # Create the database
    else:
        print('A database named {0} already exists'.format(dbname))

    # Clean up
    cur.close()
    con.close()

def count_partitions(prefix, openconnection):
   
    con = openconnection
    cur = con.cursor()
    cur.execute("select count(*) from pg_stat_user_tables where relname like " + "'" + prefix + "%';")
    count = cur.fetchone()[0]
    cur.close()

    return count