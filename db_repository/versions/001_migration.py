from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
TaskInfinitives = Table('TaskInfinitives', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user', Integer),
    Column('name', String),
    Column('tasklist', Integer),
    Column('description', String),
    Column('location', String),
    Column('starttime', String),
    Column('endtime', String),
    Column('photo', String),
    Column('period', Integer),
)

TaskList = Table('TaskList', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user', Integer),
    Column('name', String),
)

Task = Table('Task', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user', Integer),
    Column('name', String),
    Column('tasklist', Integer),
    Column('description', String),
    Column('location', String),
    Column('starttime', String),
    Column('endtime', String),
    Column('photo', String),
    Column('completion', Boolean),
)

Task = Table('Task', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user', Integer),
    Column('name', String(length=50)),
    Column('hashtag', String(length=50)),
    Column('description', String(length=1200)),
    Column('location', String(length=50)),
    Column('photo', String(length=200)),
    Column('completion', Boolean),
)

User = Table('User', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('fbid', Integer),
    Column('token', String(length=1000)),
    Column('md5token', String(length=100)),
    Column('gtoken', String(length=100)),
    Column('grtoken', String(length=100)),
    Column('gidcalendar', String(length=100)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['TaskInfinitives'].drop()
    pre_meta.tables['TaskList'].drop()
    pre_meta.tables['Task'].columns['endtime'].drop()
    pre_meta.tables['Task'].columns['starttime'].drop()
    pre_meta.tables['Task'].columns['tasklist'].drop()
    post_meta.tables['Task'].columns['hashtag'].create()
    post_meta.tables['User'].columns['gidcalendar'].create()
    post_meta.tables['User'].columns['grtoken'].create()
    post_meta.tables['User'].columns['gtoken'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['TaskInfinitives'].create()
    pre_meta.tables['TaskList'].create()
    pre_meta.tables['Task'].columns['endtime'].create()
    pre_meta.tables['Task'].columns['starttime'].create()
    pre_meta.tables['Task'].columns['tasklist'].create()
    post_meta.tables['Task'].columns['hashtag'].drop()
    post_meta.tables['User'].columns['gidcalendar'].drop()
    post_meta.tables['User'].columns['grtoken'].drop()
    post_meta.tables['User'].columns['gtoken'].drop()
