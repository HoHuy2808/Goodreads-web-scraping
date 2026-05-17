import os
from pyspark.sql import SparkSession
from ingest_data import create_snowflake_table, read_data_from_postgre, load_data_to_bronze
from transform_data import data_transform, load_data_to_silver
from load_data import (
    extract_book,
    extract_author,
    extract_book_author,
    extract_edition,
    extract_genres,
    create_table_in_sf_gold,
    load_data_to_gold
)
from dotenv import load_dotenv

load_dotenv()
# Declare private variables
sfURL = os.getenv("sfURL")
sfAccount = os.getenv("sfAccount")
sfUser = os.getenv("sfUser")
sfPassword = os.getenv("sfPassword")
db_user = os.getenv("db_user")
db_password = os.getenv("db_password")
SNOWFLAKE_SOURCE_NAME = "net.snowflake.spark.snowflake"

spark = SparkSession.builder \
    .master('local')\
    .appName("Data pipeline") \
    .config("spark.jars",
            "./spark/jars/postgresql-42.7.11.jar, ./spark/jars/spark-snowflake_2.12-2.12.0-spark_3.4.jar")\
    .getOrCreate()

sf_options_silver = {
    "sfURL": sfURL,
    "sfAccount": sfAccount,
    "sfUser": sfUser,
    "sfPassword": sfPassword,
    "sfDatabase": "DATA_WAREHOUSE",
    "sfSchema": "SILVER",
    "sfWarehouse": "COMPUTE_WH",
    "sfRole": "ACCOUNTADMIN"
}

df = spark.read \
    .format(SNOWFLAKE_SOURCE_NAME) \
    .options(**sf_options_silver) \
    .option("dbtable", "books") \
    .load()

if __name__ == "__main__":
    
    """ Bronze """
    create_snowflake_table(spark, "DATA_WAREHOUSE", "BRONZE")
    
    raw_books_df = read_data_from_postgre(spark, "books", db_user, db_password)
    
    load_data_to_bronze(raw_books_df, "books", "DATA_WAREHOUSE", "BRONZE")

    """ Silver """
    books_df = data_transform(spark, "books", "DATA_WAREHOUSE", "BRONZE")

    load_data_to_silver(books_df, "books", "DATA_WAREHOUSE", "SILVER")

    """ Gold """    
    create_table_in_sf_gold(spark, "DATA_WAREHOUSE", "GOLD")
    
    edition_df = extract_edition(df)
    genres_df = extract_genres(df)
    book_author_df = extract_book_author(df)
    author_df = extract_author(df)
    book_df = extract_book(df)
    
    load_data_to_gold(edition_df,"edition","DATA_WAREHOUSE","GOLD")
    load_data_to_gold(genres_df,"genres","DATA_WAREHOUSE","GOLD")
    load_data_to_gold(book_author_df,"book_author", "DATA_WAREHOUSE", "GOLD")
    load_data_to_gold(author_df,"author","DATA_WAREHOUSE","GOLD")
    load_data_to_gold(book_df,"book","DATA_WAREHOUSE","GOLD")