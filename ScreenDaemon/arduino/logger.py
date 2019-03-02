#!/usr/bin/env python3

import lib
import time
import sqlite3

ix=0

start = time.time()
recordList = []
sleep = 0.1

while True:
  ix += 1
  # avoiding drift.
  duration = abs(sleep * ix + start - time.time())
  time.sleep(duration)
  record = get_payload()

  # trying to avoid syncing the disk too much
  #if ix % 300 == 0:
  _SCHEMA = {
    'kv': [
       ('id', 'INTEGER PRIMARY KEY'),
       ('ts', 'INTEGER'),
       ('backlight', 'INTEGER'),
       ('fan', 'INTEGER'),
       ('temp', 'INTEGER'),
       ('current_raw', 'INTEGER'),
       ('current_normatlized', 'INTEGER'),
       ('accel_x', 'INTEGER'),
       ('accel_y', 'INTEGER'),
       ('accel_z', 'INTEGER'),
       ('gyro_x', 'INTEGER'),
       ('gyro_y', 'INTEGER'),
       ('gyro_z', 'INTEGER'),
       ('therm_read', 'INTEGER'),
       ('therm_resistance', 'INTEGER'),
       ('pitch', 'INTEGER'),
       ('roll', 'INTEGER'),
       ('yaw', 'INTEGER'),
       ('key', 'TEXT UNIQUE'),
       ('value', 'TEXT'),
       ('namespace', 'TEXT'),
       ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
     ]
  }

# Ok so if column order or type changes, this isn't found ... nor
# are we doing formal migrations where you can roll back or whatever
# because way too fancy ...
def upgrade():
  my_set = __builtins__['set']
  db = connect()

  for table, schema in list(_SCHEMA.items()):
    existing_schema = db['c'].execute('pragma table_info(%s)' % table).fetchall()
    existing_column_names = [str(row[1]) for row in existing_schema]

    our_column_names = [row[0] for row in schema]

    # print table, existing_column_names, our_column_names

    to_add = my_set(our_column_names).difference(my_set(existing_column_names))

    # These are the things we should add ... this can be an empty set, that's fine.
    for key in to_add:
      # 
      # sqlite doesn't support adding things into positional places (add column after X)
      # they just get tacked on at the end ... which is fine - you'd have to rebuild 
      # everything to achieve positional columns - that's not worth it - we just always 
      # tack on at the end as a policy in our schema and we'll be fine.
      #
      # However, given all of that, we still need the schema
      #
      our_schema = schema[our_column_names.index(key)][1]
      # print 'alter table %s add column %s %s' % (table, key, our_schema)
      db['c'].execute('alter table %s add column %s %s' % (table, key, our_schema))
      db['conn'].commit()

    to_remove = my_set(existing_column_names).difference(my_set(our_column_names))

    if len(to_remove) > 0:
      our_schema = ','.join(["%s %s" % (key, klass) for key, klass in schema])
      our_columns = ','.join(our_column_names)

      drop_column_sql = """
      CREATE TEMPORARY TABLE my_backup(%s);
      INSERT INTO my_backup SELECT %s FROM %s;
      DROP TABLE %s;
      CREATE TABLE %s(%s);
      INSERT INTO %s SELECT %s FROM my_backup;
      DROP TABLE my_backup;
      """ % (our_schema, our_columns, table, table,    table, our_schema, table, our_columns)

      for sql_line in drop_column_sql.strip().split('\n'):
        db['c'].execute(sql_line)

      db['conn'].commit()
