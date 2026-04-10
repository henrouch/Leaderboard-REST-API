# Leaderboard Database


## What tables exist?

### `users`
Stores account information for each player.

Columns:
- `id` - unique user ID
- `username` - unique username
- `password_hash` - hashed password
- `created_at` - account creation timestamp

Notes for backend:
- `username` must be unique
- passwords should not be stored as plain text

### `game_modes`
Stores the available game modes.

Columns:
- `id` - unique mode ID
- `name` - mode name
- `time_limit_seconds` - time limit for timed mode
- `lives_limit` - life limit for lives mode

Current modes:
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

## What should the backend send when storing a result?

When a game ends, the backend should insert a new row into `game_results`.

Required fields:
- `user_id`
- `mode_id`
- `hits`
- `misses`
- `accuracy`

## How to set it up locally

### Steps

** 1. Make sure PostgreSQL is installed **
Check that PostgreSQL is available in Terminal:

```bash
psql --version
```
** 2. Create Database **

```bash
psql postgres
CREATE DATABASE leaderboard_db;
\q
```

** 3. Run the Schema File **

```bash
psql leaderboard_db -f schema.sql
```
** 4. Run the Seed File **

```bash
psql leaderboard_db -f seed.sql
```
** 5. Check that everything run Well **

```bash
psql leaderboard_db
```
then run
```bash
\dt
SELECT * FROM game_modes;
```

You should see these tables:
- Users
- game_modes
- game_results

And these modes:
- Timed
- Lives

** 6. Exit PostgreSQL **
When you are done you can exit with:
```bash
\q
```
