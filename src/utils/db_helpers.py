import os
import pymysql


def get_mysql_connection():

    print("Connected to MySQL")

    return pymysql.connect(host=os.environ.get("AWS_RDS_HOST"),
                           user=os.environ.get("AWS_RDS_USER"),
                           password=os.environ.get("AWS_RDS_PASSWORD"),
                           db=os.environ.get("AWS_RDS_DB"),
                           port=int(os.environ.get("AWS_RDS_PORT")))
