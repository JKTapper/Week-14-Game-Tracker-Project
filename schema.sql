drop table if exists game;

create table game (
    game_id int generated always as identity primary key,
    game_name text,
    release_date date
);