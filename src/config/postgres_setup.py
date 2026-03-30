import psycopg
import os

from psycopg import Connection

connection :Connection

def instantiate_connection():
    """Creating PostgreSQL connection that is running in local docker """
    return psycopg.connect(host=os.getenv('POSTGRES.host'), dbname=os.getenv("POSTGRES.dbname"),
                           user=os.getenv("POSTGRES.user"), password=os.getenv("POSTGRES.password"),
                           port=os.getenv('POSTGRES.port'))


