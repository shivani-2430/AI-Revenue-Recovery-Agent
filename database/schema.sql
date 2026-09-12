-- ============================================================
-- AI REVENUE RECOVERY AGENT
-- PostgreSQL Database Schema
-- ============================================================

-- ============================================================
-- CUSTOMERS
-- ============================================================

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,

    customer_id VARCHAR(100) NOT NULL UNIQUE,

    customer_segment VARCHAR(50) NOT NULL,

    customer_since TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    successful_payments INTEGER NOT NULL DEFAULT 0,

    failed_payments INTEGER NOT NULL DEFAULT 0,

    historical_success_rate DOUBLE PRECISION NOT NULL DEFAULT 0.0,

    customer_value NUMERIC(15, 2) NOT NULL DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customers_customer_id
ON customers(customer_id);

CREATE INDEX IF NOT EXISTS idx_customers_segment
ON customers(customer_segment);


-- ============================================================
-- TRANSACTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,

    transaction_id VARCHAR(100) NOT NULL UNIQUE,

    customer_id INTEGER NOT NULL,

    amount NUMERIC(15, 2) NOT NULL,

    payment_method VARCHAR(50) NOT NULL,

    merchant_category VARCHAR(100) NOT NULL,

    status VARCHAR(30) NOT NULL,

    failure_reason VARCHAR(150),

    transaction_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    subscription_status VARCHAR(50),

    retry_count INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT fk_transactions_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_transactions_transaction_id
ON transactions(transaction_id);

CREATE INDEX IF NOT EXISTS idx_transactions_customer_id
ON transactions(customer_id);

CREATE INDEX IF NOT EXISTS idx_transactions_status
ON transactions(status);

CREATE INDEX IF NOT EXISTS idx_transactions_timestamp
ON transactions(transaction_timestamp);

CREATE INDEX IF NOT EXISTS idx_transactions_failure_reason
ON transactions(failure_reason);


-- ============================================================
-- PAYMENT ATTEMPTS
-- ============================================================

CREATE TABLE IF NOT EXISTS payment_attempts (
    id SERIAL PRIMARY KEY,

    transaction_id INTEGER NOT NULL,

    attempt_number INTEGER NOT NULL,

    attempted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    status VARCHAR(30) NOT NULL,

    failure_reason VARCHAR(150),

    response_code VARCHAR(100),

    CONSTRAINT fk_payment_attempts_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_payment_attempt
        UNIQUE (transaction_id, attempt_number)
);

CREATE INDEX IF NOT EXISTS idx_payment_attempts_transaction_id
ON payment_attempts(transaction_id);


-- ============================================================
-- RECOVERY ACTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS recovery_actions (
    id SERIAL PRIMARY KEY,

    transaction_id INTEGER NOT NULL,

    action_type VARCHAR(100) NOT NULL,

    reason TEXT NOT NULL,

    risk_score DOUBLE PRECISION NOT NULL,

    recovery_probability DOUBLE PRECISION NOT NULL,

    revenue_at_risk NUMERIC(15, 2) NOT NULL,

    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',

    guardrail_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    executed_at TIMESTAMP,

    CONSTRAINT fk_recovery_actions_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_recovery_actions_transaction_id
ON recovery_actions(transaction_id);

CREATE INDEX IF NOT EXISTS idx_recovery_actions_status
ON recovery_actions(status);

CREATE INDEX IF NOT EXISTS idx_recovery_actions_guardrail_status
ON recovery_actions(guardrail_status);


-- ============================================================
-- RECOVERY OUTCOMES
-- ============================================================

CREATE TABLE IF NOT EXISTS recovery_outcomes (
    id SERIAL PRIMARY KEY,

    transaction_id INTEGER NOT NULL,

    recovery_action_id INTEGER NOT NULL UNIQUE,

    outcome VARCHAR(50) NOT NULL,

    amount_recovered NUMERIC(15, 2) NOT NULL DEFAULT 0,

    completed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_recovery_outcomes_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_recovery_outcomes_action
        FOREIGN KEY (recovery_action_id)
        REFERENCES recovery_actions(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_recovery_outcomes_transaction_id
ON recovery_outcomes(transaction_id);

CREATE INDEX IF NOT EXISTS idx_recovery_outcomes_outcome
ON recovery_outcomes(outcome);


-- ============================================================
-- AUDIT LOGS
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,

    transaction_id INTEGER NOT NULL,

    decision_id VARCHAR(100) NOT NULL,

    decision VARCHAR(100) NOT NULL,

    reason TEXT NOT NULL,

    policy_check VARCHAR(100) NOT NULL,

    action VARCHAR(100) NOT NULL,

    result VARCHAR(100) NOT NULL,

    model_version VARCHAR(100),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_logs_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_transaction_id
ON audit_logs(transaction_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_decision_id
ON audit_logs(decision_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
ON audit_logs(created_at);


-- ============================================================
-- SUMMARY VIEW
-- ============================================================

CREATE OR REPLACE VIEW revenue_recovery_summary AS
SELECT
    COUNT(DISTINCT t.id) AS total_transactions,

    COUNT(
        DISTINCT CASE
            WHEN t.status = 'FAILED'
            THEN t.id
        END
    ) AS failed_transactions,

    COALESCE(
        SUM(ra.revenue_at_risk),
        0
    ) AS total_revenue_at_risk,

    COALESCE(
        SUM(ro.amount_recovered),
        0
    ) AS total_recovered_revenue

FROM transactions t

LEFT JOIN recovery_actions ra
    ON t.id = ra.transaction_id

LEFT JOIN recovery_outcomes ro
    ON ra.id = ro.recovery_action_id;