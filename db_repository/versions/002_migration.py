from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
task = Table('task', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user', Integer),
    Column('name', String(length=120)),
    Column('tasklist', Integer),
    Column('description', String(length=1200)),
    Column('location', String(length=250)),
    Column('starttime', String(length=10)),
    Column('endtime', String(length=10)),
    Column('frequency', String(length=10)),
    Column('photo', String(length=20)),
    Column('completion', Boolean),
)

user = Table('user', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('fbid', Integer),
    Column('token', String(length=1000)),
    Column('md5token', String(length=100)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['task'].columns['completion'].create()
    post_meta.tables['user'].columns['md5token'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['task'].columns['completion'].drop()
    post_meta.tables['user'].columns['md5token'].drop()
