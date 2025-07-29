-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS video;
DROP TABLE IF EXISTS image;
DROP TABLE IF EXISTS genre_assignment;
DROP TABLE IF EXISTS game;
DROP TABLE IF EXISTS genre;
DROP TABLE IF EXISTS publisher;
DROP TABLE IF EXISTS developer;

-- Create publisher
CREATE TABLE publisher (
    publisher_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    publisher_name TEXT
);

-- Create developer
CREATE TABLE developer (
    developer_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    developer_name TEXT
);

-- Create game 
CREATE TABLE game (
    game_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    game_name TEXT,
    release_date DATE,
    publisher_id INT,
    developer_id INT,
    game_description TEXT,
    recent_reviews_summary TEXT,
    os_requirements TEXT,
    storage_requirements TEXT,  
    price FLOAT,
    FOREIGN KEY (publisher_id) REFERENCES publisher (publisher_id),
    FOREIGN KEY (developer_id) REFERENCES developer (developer_id)
);

-- Create genre
CREATE TABLE genre (
    genre_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    genre_name TEXT
);

-- Create genre_assignment
CREATE TABLE genre_assignment (
    genre_assignment_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    genre_id INT,
    game_id INT,
    FOREIGN KEY (genre_id) REFERENCES genre (genre_id),
    FOREIGN KEY (game_id) REFERENCES game (game_id)
);

-- Create image
CREATE TABLE image (
    image_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    url_image TEXT,
    game_id INT,
    FOREIGN KEY (game_id) REFERENCES game (game_id)
);

-- Create video
CREATE TABLE video (
    video_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    url_video TEXT,
    game_id INT,
    FOREIGN KEY (game_id) REFERENCES game (game_id)
);
