 create table lookup(id integer primary key autoincrement, uid text not null, license text default null, port integer, first_seen datetime, last_seen datetime);
