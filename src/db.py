"""Kết nối PostgreSQL. Chỉ lớp repositories dùng module này."""
import psycopg
from psycopg.rows import dict_row

from src import config


def connect():
    return psycopg.connect(config.database_url(), row_factory=dict_row, connect_timeout=3)
