# Leaderboard Database

## Tables

### `users`
Stores account information for each player.

Columns:
- `id` - unique user ID
- `username` - unique username
- `password_hash` - hashed password
- `created_at` - account creation timestamp

### `game_modes`
Stores the available game modes.

Columns:
- `id` - unique mode ID
- `name` - mode name
- `time_limit_seconds` - time limit for timed mode
- `lives_limit` - life limit for lives mode

Seeded modes:
- `Timed` = 30 seconds
- `Lives` = 3 lives

### `game_results`
Stores one row for each completed game session.

Columns:
- `id` - unique result ID
- `user_id` - references `users.id`
- `mode_id` - references `game_modes.id`
- `hits` - number of successful hits
- `misses` - number of missed shots
- `accuracy` - player accuracy as a percentage
- `played_at` - timestamp of the game result

Notes:
- one user can have many game results
- one mode can have many game results
- leaderboard queries should use each player's best result

## API Contract

When a game ends, the backend should submit a result to `POST /scores`.

Required request fields:
- `username`
- `hits`
- `misses`
- `accuracy`
- `time`
- `mode` (`T`, `L`, `Timed`, or `Lives`)

The API will resolve or create the user and resolve the game mode internally.

## Endpoints

- `GET /health` - check the database connection
- `GET /modes` - list seeded game modes
- `POST /scores` - submit a game result
- `GET /leaderboard` - fetch the best result for each player
- `GET /leaderboard/{username}` - fetch one player's best result

`GET /leaderboard` accepts optional `limit`, `offset`, and `mode` query parameters.

## Local Setup

1. Make sure PostgreSQL is installed.
```bash
psql --version
```
2. Create Database

```bash
psql postgres
CREATE DATABASE leaderboard_db;
\q
```

3. Run the Schema File

```bash
psql leaderboard_db -f schema.sql
```
4. Run the Seed File

```bash
psql leaderboard_db -f seed.sql
```
5. Start the API with PostgreSQL connection settings in environment variables or `DATABASE_URL`.
