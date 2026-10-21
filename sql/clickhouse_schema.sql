-- Optional ClickHouse deployment; execute in a dedicated database.
CREATE DATABASE IF NOT EXISTS gaming_portfolio;
CREATE TABLE IF NOT EXISTS gaming_portfolio.players (
 player_id UInt64, signup_date Date, country LowCardinality(String),
 vertical LowCardinality(String), variant LowCardinality(String)
) ENGINE=MergeTree ORDER BY (variant,signup_date,player_id);
CREATE TABLE IF NOT EXISTS gaming_portfolio.settlements (
 player_id UInt64, stakes Float64, wins Float64, bet_count UInt64
) ENGINE=MergeTree ORDER BY player_id;
CREATE TABLE IF NOT EXISTS gaming_portfolio.bonuses (
 player_id UInt64, bonus_cost Float64
) ENGINE=MergeTree ORDER BY player_id;
-- Float64 used for parity with the synthetic Python data. Production money should
-- use documented fixed-point currency units and explicit settlement semantics.
