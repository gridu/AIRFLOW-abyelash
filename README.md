# AIRFLOW-abyelash
To run the project type in command line:
cd docker
# Just FIRST run
docker-compose up postgres
docker-compose up initdb
# Then comment INITDB service in docker/docker-compose.yml

# Next runs
docker-compose up
# Full rebuild after changing config - e.g airrflow.cgf
docker-compose up --build

# Configuration in AIRFLOW
2.1 create new Connection(http://localhost:8080/admin/connection/) for Postgres with name: postres_abetest
2.2 create new Variable(http://localhost:8080/admin/variable/) with
name: name_path_variable
value: /usr/local/airflow_files

3. Go  to  DAGs and enable all 4 with names GRIDU_abe*
4. Create trigger file runjobs in airflow_files/ dir
5. Trigger GRIDU_abe_trigger_dag, enjoy and wait for timestamp file in airflow_files/
