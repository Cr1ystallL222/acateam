-- SQL script to update old alphanumeric referral codes to numeric ones
-- This is optional - the bot will auto-update codes when users access escort menu

-- For PostgreSQL:
-- UPDATE users 
-- SET referral_code = FLOOR(RANDOM() * (99999999 - 100000 + 1) + 100000)::TEXT
-- WHERE referral_code IS NOT NULL 
-- AND referral_code !~ '^[0-9]+$';

-- For SQLite:
-- UPDATE users 
-- SET referral_code = CAST((ABS(RANDOM()) % 89999999 + 100000) AS TEXT)
-- WHERE referral_code IS NOT NULL 
-- AND referral_code NOT GLOB '[0-9]*';

-- Note: This script is optional. The bot will automatically update codes
-- to numeric format when users access the escort menu.
