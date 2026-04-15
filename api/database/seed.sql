INSERT INTO game_modes (name, time_limit_seconds, lives_limit)
VALUES
    ('Timed', 30, NULL),
    ('Lives', NULL, 3)
ON CONFLICT (name) DO NOTHING;