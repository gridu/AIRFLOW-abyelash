""" import operators with
from airflow.operators.postgres_custom import PostgreSQLCheckTable, PostgreSQLCountRows """

import logging

from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults
from airflow.hooks.postgres_hook import PostgresHook

log = logging.getLogger(__name__)


class PostgreSQLCheckTable(BaseOperator):
    """ operator to check table exist"""

    @apply_defaults
    def __init__(self, table_name, schema, postgres_conn_id,
                 *args, **kwargs):
        """

        :param table_name: table name
        :param schema: database schemaname, example, how to get schema name:
                        SELECT * FROM pg_tables;
        :param postgres_conn_id: Postgess connection id
        """
        self.table_name = table_name
        self.hook = PostgresHook(postgres_conn_id=postgres_conn_id)
        self.schema = schema
        super(PostgreSQLCheckTable, self).__init__(*args, **kwargs)

    def execute(self, context):

        result = self.hook.get_first(
            sql="SELECT * FROM information_schema.tables WHERE table_schema = '{}' "
                "AND table_name = '{}'; ".format(self.schema, self.table_name))
        if result:
            return True
        else:
            raise ValueError("table {} does not exist".format(self.table_name))


class PostgreSQLCountRows(BaseOperator):
    """ operator to check table exist"""

    @apply_defaults
    def __init__(self, table_name, postgres_conn_id,
                 *args, **kwargs):
        """

        :param table_name: table name
        :param postgres_conn_id: Postgess connection id
        """
        self.table_name = table_name
        self.hook = PostgresHook(postgres_conn_id=postgres_conn_id)
        super(PostgreSQLCountRows, self).__init__(*args, **kwargs)

    def execute(self, context):
        result = self.hook.get_first(
            sql="SELECT COUNT(*) FROM {};".format(self.table_name))
        log.info("Result: {}".format(result))
        return result


class PostgreSQLCustomOperatorsPlugin(AirflowPlugin):
    name = "postgres_abe_custom"
    operators = [PostgreSQLCheckTable, PostgreSQLCountRows]