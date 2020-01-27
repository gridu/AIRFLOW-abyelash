docker-compose up postgres
#Just FIRST time
#docker-compose up initdb
docker-compose up scheduler webserver
#Full rebuild after changing config - e.g airrflow.cgf
docker-compose up --build
#      - ../dags:/usr/local/airflow/dags
#      - ./airflow_files:/usr/local/airflow_files
