from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
Task = Table('Task', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user', Integer),
    Column('name', String),
    Column('hashtag', String),
    Column('description', String),
    Column('location', String),
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
    Column('pictureurl', String(length=200)),
    Column('completion', Boolean),
    Column('timecompleted', Integer),
)

User = Table('User', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=100)),
    Column('profilepic', String(length=1000)),
    Column('fbid', Integer),
    Column('token', String(length=1000)),
    Column('md5token', String(length=100)),
    Column('gtoken', String(length=100)),
    Column('grtoken', String(length=100)),
    Column('lastupdatedtoken', Integer),
    Column('gidcalendar', String(length=100)),
    Column('privacy', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['Task'].columns['photo'].drop()
    post_meta.tables['Task'].columns['pictureurl'].create()
    post_meta.tables['Task'].columns['timecompleted'].create()
    post_meta.tables['User'].columns['name'].create()
    post_meta.tables['User'].columns['privacy'].create()
    post_meta.tables['User'].columns['profilepic'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['Task'].columns['photo'].create()
    post_meta.tables['Task'].columns['pictureurl'].drop()
    post_meta.tables['Task'].columns['timecompleted'].drop()
    post_meta.tables['User'].columns['name'].drop()
    post_meta.tables['User'].columns['privacy'].drop()
    post_meta.tables['User'].columns['profilepic'].drop()
