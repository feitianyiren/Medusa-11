Medusa
=======

The MEDia USage Assistant.

Database Creation
-----------

CREATE TABLE media (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, paths TEXT, name_one TEXT, name_two TEXT, name_three TEXT, name_four TEXT, year INTEGER, extension TEXT, modified INTEGER);

CREATE TABLE viewed (id TEXT, viewed INTEGER, elapsed INTEGER);
