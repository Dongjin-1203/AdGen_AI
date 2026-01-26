from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 기존 import들 아래에 추가
import sys
import os
from pathlib import Path

# backend 디렉토리를 Python path에 추가
sys.path.append(str(Path(__file__).parent.parent))

# 우리 모델 import
from config import settings
from app.db.base import Base
# 모든 모델 import (Alembic autogenerate를 위해 필요)
from app.models import (
    User,
    UserContent,
    GenerationHistory,
    AIPrediction,
    UserCorrection,
    RewardScore,
    AdCaption,
    CaptionCorrection,
    AdCopyHistory
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# ===== DATABASE_URL 로드 및 % 이스케이프 =====
db_url = settings.CLOUD_SQL_URL
# ConfigParser는 % 기호를 interpolation 구문으로 해석하므로 %% 로 변환
if db_url:
    db_url_escaped = db_url.replace('%', '%%')
    config.set_main_option("sqlalchemy.url", db_url_escaped)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()