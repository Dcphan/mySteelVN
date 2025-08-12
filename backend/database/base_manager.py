import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from sqlalchemy import create_engine
from contextlib import contextmanager


class BaseDBManager:
    def __init__(self, config: dict):
        self.config = config
        self.engine = None

    # Raw connection for psycopg2 (non-SQLAlchemy use)
    def connect(self):
        return psycopg2.connect(**self.config)

    # SQLAlchemy engine connection (used with pandas or insert functions)
    def _create_engine(self):
        if self.engine is None:
            url = (
                f"postgresql+psycopg2://{self.config['user']}:{self.config['password']}"
                f"@{self.config['host']}/{self.config['dbname']}?sslmode={self.config.get('sslmode', 'require')}"
            )
            self.engine = create_engine(url, pool_pre_ping=True)

    # Properly dispose SQLAlchemy engine
    def dispose(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None

    # Context manager for raw psycopg2 cursor (auto-commits & closes)
    @contextmanager
    def get_cursor(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"❌ Cursor operation failed: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    # Insert with ON CONFLICT DO NOTHING (for deduplication)
    def _insert_on_conflict_do_nothing(self, df: pd.DataFrame, table_name: str, columns: list[str]):
        if df.empty:
            print(f"⚠️ No new rows for '{table_name}'.")
            return

        self._create_engine()  # Ensure engine is ready

        conn = self.engine.raw_connection()
        try:
            cur = conn.cursor()
            values = df[columns].fillna('unknown').values.tolist()
            query = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES %s
                ON CONFLICT DO NOTHING
            """
            execute_values(cur, query, values)
            conn.commit()
            cur.close()
            print(f"✅ Inserted (deduplicated) {len(values)} rows into '{table_name}'.")
        except Exception as e:
            print(f"❌ Error inserting into '{table_name}' with ON CONFLICT: {e}")
        finally:
            conn.close()


    # Bulk insert without deduplication
    def _bulk_insert_dataframe(self, table_name: str, df: pd.DataFrame):
        if df.empty:
            print(f"⚠️ No data to insert into '{table_name}'.")
            return

        self._create_engine()

        conn = None
        cursor = None
        try:
            conn = self.engine.raw_connection()
            cursor = conn.cursor()

            columns = list(df.columns)
            values = df.to_records(index=False).tolist()

            insert_query = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES %s
            """

            execute_values(cursor, insert_query, values)
            conn.commit()
            print(f"✅ Inserted {len(df)} rows into '{table_name}'.")
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ Error bulk inserting into '{table_name}': {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def build_value_select_clause(self, value_fields):
        mapping = {
            "amount": "ROUND(SUM(t.amount)::numeric, 2) AS amount",
            "quantity": "ROUND(SUM(t.quantity)::numeric, 0) AS quantity",
        }
        condition_not_nan = {
            "amount": "t.amount <> 'NaN'",
            "quantity": "t.quantity <> 'NaN'"
        }
        return [", ".join([mapping[f] for f in value_fields if f in mapping]), "AND ".join([condition_not_nan[f] for f in value_fields if f in condition_not_nan])]
