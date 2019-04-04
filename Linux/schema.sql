create table history(
	id integer primary key autoincrement, 
	created_at datetime default current_timestamp,
	datatype integer default null,
	value text default null
);
