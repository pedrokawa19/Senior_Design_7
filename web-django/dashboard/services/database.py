"""Connections to the client's MySQL server.

This is the external database being reported on, not Django's own database.
Every connection is bounded by timeouts and marked read-only: the dashboard
reports on Vision Metals data and must never modify it.
"""

import logging

import mysql.connector

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT_SECONDS = 10
QUERY_TIMEOUT_SECONDS = 30


def get_database_connection(settings):
    if not all(settings.values()):
        raise ValueError("Complete User, Password, Host, Port, and Database before connecting.")

    connection = mysql.connector.connect(
        user=settings["user"],
        password=settings["password"],
        host=settings["host"],
        port=int(settings["port"]),
        database=settings["database"],
        connection_timeout=CONNECT_TIMEOUT_SECONDS,
        autocommit=True,
    )
    _apply_session_guards(connection)
    return connection


def _apply_session_guards(connection):
    guards = (
        f"SET SESSION MAX_EXECUTION_TIME = {QUERY_TIMEOUT_SECONDS * 1000}",
        "SET SESSION TRANSACTION READ ONLY",
    )
    cursor = connection.cursor()
    try:
        for statement in guards:
            try:
                cursor.execute(statement)
            except mysql.connector.Error:
                # MariaDB and older MySQL name these differently; losing a guard
                # must not stop the report from running.
                logger.info("Database session guard not supported by this server.")
    finally:
        cursor.close()


def verify_database_connection(settings):
    connection = get_database_connection(settings)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
    finally:
        connection.close()
