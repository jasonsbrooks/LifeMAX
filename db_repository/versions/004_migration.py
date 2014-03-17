from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
LifeMaxAuth = Table('LifeMaxAuth', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('gtoken', String(length=100)),
    Column('grtoken', String(length=100)),
    Column('lastupdatedtoken', Integer),
)

User = Table('User', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('fbid', Integer),
    Column('token', String(length=1000)),
    Column('md5token', String(length=100)),
    Column('gtoken', String(length=100)),
    Column('grtoken', String(length=100)),
    Column('lastupdatedtoken', Integer),
    Column('gidcalendar', String(length=100)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['LifeMaxAuth'].columns['lastupdatedtoken'].create()
    post_meta.tables['User'].columns['lastupdatedtoken'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['LifeMaxAuth'].columns['lastupdatedtoken'].drop()
    post_meta.tables['User'].columns['lastupdatedtoken'].drop()
