import contextlib

from sqlalchemy import create_engine as sqla_create_engine
from sqlalchemy.engine import url as sqla_url
from sqlalchemy.ext.declarative import declarative_base as sqla_base_model
from sqlalchemy.orm import sessionmaker as sqla_sessionmaker
from sqlalchemy.orm.session import Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError as DatabaseError


__all__ = ["MySQLDatabase", "Model",]

Model = sqla_base_model()


class MySQLDatabase:
    def __init__(self, user, password, database, host=None, port=0, **kwargs):
        """
        Create MySQL Database Handler.
        :param opt:
        :param kwargs:
            pool_size | int, default 5
            pool_pre_ping | bool , default True
            echo | bool, default False
        """
        driver = "mysql+pymysql"
        host = host or "localhost"
        port = port or 3306

        self._engine = None
        self._session_cls = None

        connection_params = {
            "poolclass": QueuePool,
            "pool_size": kwargs.pop("pool_size", 5),
            "pool_pre_ping": kwargs.pop("pool_pre_ping", True),
            "echo": kwargs.pop("echo_sql", False),
        }

        url = sqla_url.URL(
            drivername=driver,
            username=user,
            password=password,
            host=host,
            port=port,
            database=database,
        )
        self._engine = sqla_create_engine(url, **connection_params)
        self._session_cls = sqla_sessionmaker(bind=self._engine, autocommit=False, autoflush=True)
        Model.metadata.create_all(self._engine)

    def close(self):
        if self._engine and hasattr(self._engine, "dispose"):
            self._engine.dispose()
        self._engine = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    @contextlib.contextmanager
    def _session(self) -> Session:
        with self._session_cls() as session:
            try:
                session.expire_on_commit = False
                with session.begin():
                    yield session
                session.expunge_all()
                session.commit()
            except Exception as err:
                session.rollback()
                raise err

    def add(self, table_class: Model, records: list) -> int:
        inserted_count = 0
        legal_records = [r for r in records if isinstance(r, table_class)]
        with self._session() as session:
            for record in legal_records:
                session.add(record)
                inserted_count += 1
        return inserted_count

    def delete(self, table_class: Model, wheres: dict) -> int:
        with self._session() as session:
            cursor = session.query(table_class)
            for field, value in wheres.items():
                if isinstance(value, list):
                    cursor = cursor.filter(field.in_(value))
                else:
                    cursor = cursor.filter(field == value)
            return cursor.delete(synchronize_session=False)

    def update(self, table_class: Model, wheres: dict, updates: dict) -> int:
        modified_count = 0
        with self._session() as session:
            cursor = session.query(table_class)
            # query
            for field, value in wheres.items():
                if isinstance(value, list):
                    cursor = cursor.filter(field.in_(value))
                else:
                    cursor = cursor.filter(field == value)
            # modify
            for record in cursor.all():
                modified_count += 1
                for field, new_value in updates.items():
                    if hasattr(record, field.name):
                        setattr(record, field.name, new_value)
        return modified_count

    def query(self, table_class: Model, wheres: dict, order_field=None, limit=None) -> list[Model]:
        with self._session() as session:
            # query
            cursor = session.query(table_class)
            for field, value in wheres.items():
                if isinstance(value, list):
                    cursor = cursor.filter(field.in_(value))
                else:
                    cursor = cursor.filter(field == value)
            # should order by ?
            if order_field:
                cursor = cursor.order_by(order_field)

            return [cursor.first()] if limit and limit == 1 else [row for row in cursor.all() if row]
