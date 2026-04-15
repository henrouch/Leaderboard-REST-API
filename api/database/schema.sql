CREATE TABLE IF NOT EXISTS users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS game_modes (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(20) NOT NULL UNIQUE,
    time_limit_seconds INTEGER,
    lives_limit INTEGER
);

CREATE TABLE IF NOT EXISTS game_results (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    mode_id INTEGER NOT NULL,
    hits INTEGER NOT NULL CHECK (hits >= 0),
    misses INTEGER NOT NULL CHECK (misses >= 0),
    accuracy NUMERIC(5,2) NOT NULL CHECK (accuracy >= 0 AND accuracy <= 100),
    played_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (mode_id) REFERENCES game_modes(id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_game_results_user_id ON game_results(user_id);
CREATE INDEX IF NOT EXISTS idx_game_results_mode_id ON game_results(mode_id);
CREATE INDEX IF NOT EXISTS idx_game_results_played_at ON game_results(played_at);
CREATE INDEX IF NOT EXISTS idx_game_results_mode_rank ON game_results(mode_id, hits DESC, accuracy DESC, misses ASC);
