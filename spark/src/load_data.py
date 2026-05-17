from pyspark.sql.functions import *
from pyspark.sql.types import StructType, StructField, ArrayType, IntegerType
from pyspark.sql import SparkSession
import os
from dotenv import load_dotenv
load_dotenv()
SNOWFLAKE_SOURCE_NAME = "net.snowflake.spark.snowflake"

# Declare private variables
sfURL = os.getenv("sfURL")
sfAccount = os.getenv("sfAccount")
sfUser = os.getenv("sfUser")
sfPassword = os.getenv("sfPassword")
db_user = os.getenv("db_user")
db_password = os.getenv("db_password")

def extract_author(df):
    author_schema = ArrayType(
        StructType([
            StructField("author_id", StringType(), True),
            StructField("author_name", StringType(), True)
        ])
    )
    # Author table
    df = df.withColumn(
        "AUTHORS_PARSED",
        from_json(col("AUTHORS"), author_schema)
    )

    authors_df = df.select(
        col("BOOK_ID"),
        explode(col("AUTHORS_PARSED")).alias("AUTHOR")
    ).select(
        col("AUTHOR.author_id").alias("AUTHOR_ID"),
        col("AUTHOR.author_name").alias("AUTHOR_NAME"),
    ).distinct()

    return authors_df

def extract_book(df):
    # Book table 
    book_df = df.select(
        col("BOOK_ID").alias("book_id"),
        col("TITLE").alias("title"),
        col("URL").alias("url"),
        col("DESCRIPTION").alias("description"),
    ).distinct()

    return book_df

def extract_book_author(df):
    author_schema = ArrayType(
        StructType([
            StructField("author_id", StringType(), True),
            StructField("author_name", StringType(), True)
        ])
    )
    df = df.withColumn(
        "AUTHORS_PARSED", 
        from_json(col("AUTHORS"), author_schema)
        )
    
    book_author_df = df.select(
        col("BOOK_ID").alias("book_id"),
        explode(col("AUTHORS_PARSED")).alias("AUTHOR")
    ).select(
        col("book_id"),
        col("AUTHOR.author_id").cast(IntegerType()).alias("author_id"),
    ).distinct()
    
    return book_author_df

def extract_edition(df):
    # Edition table
    edition_df = df.select(
        col("BOOK_ID").alias("book_id"),
        col("ISBN").alias("isbn"),
        col("PUBLISH_DATE").alias("publish_date"),
        col("PUBLISHER").alias("publisher"),
        col("FORMAT").alias("format"),
        col("PAGES").alias("pages"),
        col("LANGUAGE").alias("language"),
        col("PRICE").alias("price"),
        col("RATING").alias("average_rating"),
        col("TOTAL_RATINGS").alias("total_ratings"),
        col("TOTAL_REVIEWS").alias("total_reviews"),
        col("AWARDS").alias("awards")
    ).distinct()

    return edition_df

def extract_genres(df):
    # Genres table
    genres_df = df.withColumn(
        "genre",
        explode(split(col("GENRES"), ",\\s*"))
    ).select(
        col("BOOK_ID").alias("book_id"),
        trim(col("genre")).alias("genre")
    )
    
    return genres_df

def create_table_in_sf_gold(spark, sf_database, sf_schema):
    sf_options_gold = {
        "sfURL": sfURL,
        "sfAccount": sfAccount,
        "sfUser": sfUser,
        "sfPassword": sfPassword,
        "sfDatabase": sf_database, #"DATA_WAREHOUSE",
        "sfSchema": sf_schema, #"GOLD",
        "sfWarehouse": "COMPUTE_WH",
        "sfRole": "ACCOUNTADMIN"
    }
    queries = [

        """
        CREATE TABLE IF NOT EXISTS DATA_WAREHOUSE.GOLD.book (
            book_id BIGINT,
            title VARCHAR,
            url VARCHAR,
            description VARCHAR,
            CONSTRAINT pk_book PRIMARY KEY (book_id)
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS DATA_WAREHOUSE.GOLD.author (
            author_id INT,
            author_name VARCHAR,
            CONSTRAINT pk_author PRIMARY KEY (author_id)
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS DATA_WAREHOUSE.GOLD.book_author (
            book_id BIGINT,
            author_id INT,
            CONSTRAINT pk_book_author PRIMARY KEY (book_id, author_id),
            CONSTRAINT fk_ab_book
                FOREIGN KEY (book_id)
                REFERENCES DATA_WAREHOUSE.GOLD.book(book_id),

            CONSTRAINT fk_ab_author
                FOREIGN KEY (author_id)
                REFERENCES DATA_WAREHOUSE.GOLD.author(author_id)
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS DATA_WAREHOUSE.GOLD.edition (
            book_id BIGINT,
            isbn VARCHAR,
            publish_date DATE,
            publisher VARCHAR,
            format VARCHAR,
            pages INT,
            language VARCHAR,
            price NUMERIC(10,2),
            average_rating FLOAT,
            total_rating INT,
            total_reviews INT,
            awards VARCHAR,

            CONSTRAINT pk_edition PRIMARY KEY (book_id),

            CONSTRAINT fk_ed_book
                FOREIGN KEY (book_id)
                REFERENCES DATA_WAREHOUSE.GOLD.book(book_id)
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS DATA_WAREHOUSE.GOLD.genres (
            book_id BIGINT,
            genre VARCHAR,

            CONSTRAINT pk_genres PRIMARY KEY (book_id),

            CONSTRAINT fk_genre_book
                FOREIGN KEY (book_id)
                REFERENCES DATA_WAREHOUSE.GOLD.book(book_id)
        )
        """
    ]

    for query in queries:
        spark._jvm.net.snowflake.spark.snowflake.Utils.runQuery(
            sf_options_gold,
            query
        )

def load_data_to_gold(df, table, sf_database, sf_schema):
    sf_options_gold = {
        "sfURL": sfURL,
        "sfAccount": sfAccount,
        "sfUser": sfUser,
        "sfPassword": sfPassword,
        "sfDatabase": sf_database, #"DATA_WAREHOUSE",
        "sfSchema": sf_schema, #"GOLD",
        "sfWarehouse": "COMPUTE_WH",
        "sfRole": "ACCOUNTADMIN"
    }

    df.write\
        .format(SNOWFLAKE_SOURCE_NAME)\
        .options(**sf_options_gold)\
        .option("dbtable", table)\
        .mode('append')\
        .save()
    
