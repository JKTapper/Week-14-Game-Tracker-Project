PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

CREATE TABLE store (
    store_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_name TEXT NOT NULL UNIQUE
);

CREATE TABLE publisher (
    publisher_id INTEGER PRIMARY KEY,
    publisher_name TEXT NOT NULL UNIQUE
);

CREATE TABLE developer (
    developer_id INTEGER PRIMARY KEY,
    developer_name TEXT NOT NULL UNIQUE
);

CREATE TABLE genre (
    genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
    genre_name TEXT NOT NULL UNIQUE
);

CREATE TABLE game (
    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_name TEXT NOT NULL,
    app_id INTEGER UNIQUE NOT NULL,
    store_id INTEGER NOT NULL,
    release_date TEXT,
    game_description TEXT,
    recent_reviews_summary TEXT,
    os_requirements TEXT,
    storage_requirements TEXT,
    price REAL,
    FOREIGN KEY (store_id) REFERENCES store (store_id)
);

CREATE TABLE genre_assignment (
    genre_assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    genre_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    FOREIGN KEY (genre_id) REFERENCES genre (genre_id),
    FOREIGN KEY (game_id) REFERENCES game (game_id)
);

CREATE TABLE developer_assignment (
    developer_assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    developer_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    FOREIGN KEY (developer_id) REFERENCES developer (developer_id),
    FOREIGN KEY (game_id) REFERENCES game (game_id)
);

CREATE TABLE publisher_assignment (
    publisher_assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    publisher_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    FOREIGN KEY (publisher_id) REFERENCES publisher (publisher_id),
    FOREIGN KEY (game_id) REFERENCES game (game_id)
);

COMMIT;

PRAGMA foreign_keys = ON;