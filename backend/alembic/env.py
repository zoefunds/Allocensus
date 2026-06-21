import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import *  # noqa: F401,F403 — import all models for autogenerate

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

_raw_url = os.getenv("DATABASE_URL", "")
# Normalize to postgresql+asyncpg:// for async engine
if _raw_url.startswith("postgres://"):
    _raw_url = "postgresql+asyncpg://" + _raw_url[len("postgres://"):]
elif _raw_url.startswith("postgresql://"):
    _raw_url = "postgresql+asyncpg://" + _raw_url[len("postgresql://"):]
# Strip sslmode=disable (not understood by asyncpg)
_raw_url = _raw_url.replace("?sslmode=disable", "").replace("&sslmode=disable", "")
DATABASE_URL = _raw_url

_CONNECT_ARGS: dict = {}
if "flycast" in DATABASE_URL or not DATABASE_URL:
    _CONNECT_ARGS["ssl"] = False

if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    config_section = config.get_section(config.config_ini_section, {})
    config_section["sqlalchemy.url"] = DATABASE_URL
    connectable = async_engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=_CONNECT_ARGS,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
