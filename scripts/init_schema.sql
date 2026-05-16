-- rad-lab research SQLite schema
-- Run: sqlite3 research/index.sqlite < scripts/init_schema.sql

CREATE TABLE IF NOT EXISTS hypotheses (
    id TEXT PRIMARY KEY,
    mission TEXT NOT NULL,
    title TEXT NOT NULL,
    h0 TEXT, h1 TEXT, predictions TEXT,
    metric_primary TEXT,
    status TEXT CHECK(status IN ('backlog','active','validated','discarded','archived')),
    priority_score REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    rationale TEXT, md_path TEXT
);

CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    hypothesis_id TEXT REFERENCES hypotheses(id),
    plan_md_path TEXT,
    in_sample_period TEXT,
    validation_period TEXT,
    oos_period TEXT,
    stat_test TEXT,
    stopping_criteria TEXT,
    created_at TEXT NOT NULL,
    status TEXT CHECK(status IN ('queued','running','done','failed','cancelled')),
    params_json TEXT
);

CREATE TABLE IF NOT EXISTS backtest_results (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL REFERENCES experiments(id),
    ran_at TEXT NOT NULL,
    dataset_id TEXT,
    oos_used INTEGER NOT NULL DEFAULT 0,
    profit_factor REAL, win_rate REAL,
    max_drawdown REAL, sharpe_ratio REAL,
    n_trades INTEGER, raw_metrics_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_br_experiment ON backtest_results(experiment_id);

CREATE TABLE IF NOT EXISTS verdicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id TEXT REFERENCES experiments(id),
    decided_at TEXT NOT NULL,
    verdict TEXT CHECK(verdict IN ('ship','discard','iterate','review')),
    rationale TEXT, decided_by TEXT
);

CREATE TABLE IF NOT EXISTS inbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    action_url TEXT,
    status TEXT CHECK(status IN ('pending','approved','rejected','deferred','expired')),
    priority TEXT CHECK(priority IN ('critical','high','normal','low')),
    decided_at TEXT, decided_by TEXT
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    mission TEXT,
    severity TEXT CHECK(severity IN ('info','warning','critical')),
    title TEXT NOT NULL, description TEXT,
    raw_data_json TEXT, md_path TEXT
);

CREATE TABLE IF NOT EXISTS agent_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    invoked_at TEXT NOT NULL,
    duration_ms INTEGER,
    tokens_input INTEGER, tokens_output INTEGER,
    router_used TEXT, success INTEGER, error_message TEXT
);

CREATE TABLE IF NOT EXISTS budget_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    agent_id TEXT, mission TEXT,
    tokens_consumed INTEGER, router TEXT, cost_usd REAL,
    cumulative_day_tokens INTEGER, cumulative_month_tokens INTEGER
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL, ended_at TEXT,
    agent_id TEXT, mission TEXT,
    status TEXT, payload_json TEXT
);

CREATE TABLE IF NOT EXISTS outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    type TEXT, payload_json TEXT,
    status TEXT CHECK(status IN ('pending','sent','failed'))
);
