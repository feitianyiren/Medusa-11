Medusa
======

The MEDia USage Assistant.

Database
======

CREATE TABLE receivers (id INTEGER PRIMARY KEY AUTOINCREMENT, host TEXT, name TEXT, status TEXT, media_directory TEXT, media_info TEXT);

CREATE TABLE viewed (media_directory TEXT, media_info TEXT, date_played TEXT, time_viewed INTEGER);

CREATE TABLE film (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, title_clean TEXT, director TEXT, director_clean TEXT, year INTEGER, extension TEXT, date_added TEXT);

CREATE TABLE television (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, show TEXT, year INTEGER, season INTEGER, episode INTEGER, extension TEXT, date_added TEXT);
