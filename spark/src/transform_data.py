from pyspark.sql.functions import (
    col, 
    to_date, 
    regexp_replace, 
    from_json
)
from pyspark.sql.types import (
    FloatType, 
    DoubleType, 
    IntegerType, 
    LongType, 
    StructType, 
    StructField, 
    ArrayType,
    StringType
)
from pyspark.sql.functions import *
from dotenv import load_dotenv
import os
load_dotenv()

# Declare private variables
sfURL = os.getenv("sfURL")
sfAccount = os.getenv("sfAccount")
sfUser = os.getenv("sfUser")
sfPassword = os.getenv("sfPassword")
db_user = os.getenv("db_user")
db_password = os.getenv("db_password")
SNOWFLAKE_SOURCE_NAME = "net.snowflake.spark.snowflake"

def data_transform(spark, table, sf_database, sf_schema):
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
    df = spark.read \
        .format(SNOWFLAKE_SOURCE_NAME) \
        .options(**sfOptions) \
        .option("dbtable", table) \
        .load()


    # Pulish date 
    df = df.withColumn(
        "PUBLISH_DATE",
        to_date(col("PUBLISH_DATE"), "MMMM d, yyyy")
    )
    
    # Parse Authors column from json  
    author_schema = ArrayType(
        StructType([
            StructField("author_id", StringType(), True),
            StructField("author_name", StringType(), True)
        ])
    )

    df = df.withColumn(
        "AUTHOR_PARSED",
        from_json(col("AUTHORS"), author_schema)
    )

    # clean author names
    df = df.withColumn(
        "AUTHOR_PARSED",
        transform(
            col("AUTHOR_PARSED"),
            lambda x: struct(
                x["author_id"].alias("author_id"),
                trim(
                    regexp_replace(
                        x["author_name"],
                        r"\s+",
                        " "
                    )
                ).alias("author_name")
            )
        )
    )

    df = df.withColumn(
        "AUTHORS", 
        col("AUTHOR_PARSED")
    ).drop("AUTHOR_PARSED")

    # Parse Awards column from json
    award_schema = ArrayType(
        StructType([
            StructField("year_won", StringType(), True),
            StructField("award_name", StringType(), True)
        ])
    )

    df = df.withColumn(
        "AWARD_PARSED",
        from_json(col("AWARDS"), award_schema)
    )

    df = df.withColumn(
        "AWARDS", 
        col("AWARD_PARSED")
    ).drop("AWARD_PARSED")

    # Number columns process
    df = df.withColumn(
            'BOOK_ID',
            col('BOOK_ID').cast(LongType())
            )\
        .withColumn(
            'PRICE',
            col('PRICE').cast(DoubleType())
        )\
        .withColumn(
            'RATING', 
            col('RATING').cast(FloatType())
        )\
        .withColumn(
            'TOTAL_RATINGS', 
            regexp_replace(col('TOTAL_RATINGS'), ",", "").cast(IntegerType())
        )\
        .withColumn(
            'TOTAL_REVIEWS', 
            regexp_replace(col('TOTAL_REVIEWS'), ",","").cast(IntegerType())
        )\
        .withColumn(
            'PAGES', 
            col('PAGES').cast(IntegerType())
        )

    return df

def load_data_to_silver(df, table, sf_database, sf_schema):
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