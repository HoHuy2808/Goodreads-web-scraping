import json

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
from crawl_data import get_data

start_book_id = 251
end_book_id = 300

def insert_book_data_to_postgres(**kwargs):
    ti = kwargs['ti']
    xcom_data = ti.xcom_pull(key='book_data',task_ids='crawl_book_data')
    if not xcom_data:
        raise ValueError("No book data found")
    
    books = json.loads(xcom_data)

    postgres_hook = PostgresHook(postgres_conn_id='postgres_localhost')
    insert_query="""
    INSERT INTO books (
        book_id,
        title,
        isbn,
        format,
        publisher,
        publish_date,
        genres,
        price,
        language,
        rating,
        total_ratings,
        total_reviews,
        pages,
        authors,
        awards,
        description,
        url
    )
    VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s
    )
    ON CONFLICT (book_id)
    DO NOTHING;
    """
    for book in books:
        postgres_hook.run(insert_query,parameters=(
            book['Goodreads ID'],
            book['name'],
            book['isbn'],
            book['format'],
            book['publisher'],
            book['publish_date'],
            book['genres'],
            book['price'],
            book['language'],
            book['rating'],
            book['total_ratings'],
            book['total_reviews'],
            book['pages'],
            json.dumps(book['authors']),
            json.dumps(book['awards']),
            book['description'],
            book['url']
        ))
    

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2026, 5, 17),
    # 'end_date': datetime(2026, 5, 10),
    'retries': 5,
    'retry_delay': timedelta(minutes=1)
}

with DAG(
    default_args=default_args,
    dag_id='crawl_and_load_data_into_db',
    description='crawl book data from goodreads and openlibrary',
    schedule='@daily',
    catchup=False
) as dag:

    # Crawl book data task
    crawl_data = PythonOperator(
        task_id=f'crawl_book_data',
        python_callable=get_data,
        op_kwargs={
            'start': start_book_id,
            'end': end_book_id
        }
    )

    # Create postgres table
    create_table = PostgresOperator(
        task_id='create_postgres_table',
        postgres_conn_id='postgres_localhost',
        sql="""
        DROP TABLE IF EXISTS books;
        CREATE TABLE books (
            book_id BIGINT PRIMARY KEY,
            title TEXT,
            isbn TEXT,
            format TEXT,
            publisher TEXT,
            publish_date TEXT,
            genres TEXT,
            price TEXT,
            language TEXT,
            rating TEXT,
            total_ratings TEXT,
            total_reviews TEXT,
            pages TEXT,
            authors JSONB,
            awards JSONB,
            description TEXT,
            url TEXT
        );
        """
    )

    # Insert book data to postgres task
    insert_book_data = PythonOperator(
        task_id='insert_book_data',
        python_callable=insert_book_data_to_postgres,
        dag=dag
    )

# crawl_tasks >> create_table >> insert_book_data 
crawl_data >> create_table >> insert_book_data 