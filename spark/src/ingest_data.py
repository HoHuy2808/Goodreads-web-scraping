import os
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
def create_snowflake_table(spark, sf_database, sf_schema):
    sfOptions = {
        "sfURL": sfURL,
        "sfAccount": sfAccount,
        "sfUser": sfUser,
        "sfPassword": sfPassword,
        "sfDatabase": sf_database, #"DATA_WAREHOUSE"
        "sfSchema": sf_schema, #"BRONZE"
        "sfWarehouse": "COMPUTE_WH",
        "sfRole": "ACCOUNTADMIN"
    }

    create_table = """
    CREATE TABLE IF NOT EXISTS DATA_WAREHOUSE.BRONZE.books (
        book_id NUMBER,
        title STRING,
        isbn STRING,
        format STRING,
        publisher STRING,
        publish_date STRING,
        genres STRING,
        price STRING,
        language STRING,
        rating STRING,
        total_ratings STRING,
        total_reviews STRING,
        pages STRING,
        authors VARIANT,
        awards VARIANT,
        description STRING,
        url STRING,
        primary key(book_id)
    );
    """
        
    spark._jvm.net.snowflake.spark.snowflake.Utils.runQuery(sfOptions, create_table)


def read_data_from_postgre(spark, table, db_user, db_password):

    query = f"""(SELECT * FROM {table}) AS BOOKS"""

    df = spark.read \
        .format("jdbc")\
        .option("url", "jdbc:postgresql://localhost:5432/goodreads") \
        .option("dbtable", query) \
        .option("user", db_user) \
        .option("password", db_password) \
        .option("driver", "org.postgresql.Driver") \
        .load()
    
    return df

def load_data_to_bronze(df, table, sf_database, sf_schema):
    sfOptions = {
        "sfURL": sfURL,
        "sfAccount": sfAccount,
        "sfUser": sfUser,
        "sfPassword": sfPassword,
        "sfDatabase": sf_database,
        "sfSchema": sf_schema,
        "sfWarehouse": "COMPUTE_WH",
        "sfRole": "ACCOUNTADMIN"
        }
    
    df.write\
        .format(SNOWFLAKE_SOURCE_NAME)\
        .options(**sfOptions)\
        .option("dbtable", table)\
        .mode('overwrite')\
        .save()
