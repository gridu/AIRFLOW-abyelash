#Just FIRST run
docker-compose up postgres
docker-compose up initdb
# Then comment INITDB service in docker/docker-compose.yml
#Next runs
docker-compose up
#Full rebuild after changing config - e.g airrflow.cgf
docker-compose up --build
#      - ../dags:/usr/local/airflow/dags
#      - ./airflow_files:/usr/local/airflow_files
