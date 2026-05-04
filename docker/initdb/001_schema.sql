CREATE TABLE IF NOT EXISTS companies (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  normalized_name VARCHAR(255) NOT NULL,
  credit_code VARCHAR(32) NULL,
  aliases TEXT NULL,
  industry VARCHAR(64) NOT NULL DEFAULT '综合/其他',
  city VARCHAR(64) NOT NULL DEFAULT '北京',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_credit_code (credit_code),
  KEY idx_normalized_name (normalized_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS funding_events (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  company_id BIGINT UNSIGNED NOT NULL,
  event_date DATE NULL,
  round VARCHAR(64) NULL,
  amount VARCHAR(64) NULL,
  currency VARCHAR(16) NULL,
  investors TEXT NULL,
  source_type VARCHAR(32) NOT NULL,
  source_url TEXT NULL,
  raw_text MEDIUMTEXT NULL,
  fingerprint CHAR(64) NOT NULL,
  confidence DECIMAL(4,3) NOT NULL DEFAULT 0.900,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_fingerprint (fingerprint),
  KEY idx_company_date (company_id, event_date),
  CONSTRAINT fk_funding_company FOREIGN KEY (company_id) REFERENCES companies(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS hiring_snapshots (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  company_id BIGINT UNSIGNED NOT NULL,
  snapshot_date DATE NOT NULL,
  channel VARCHAR(64) NOT NULL,
  open_jobs_count INT NOT NULL,
  categories TEXT NULL,
  keywords TEXT NULL,
  source_url TEXT NULL,
  raw_payload MEDIUMTEXT NULL,
  confidence DECIMAL(4,3) NOT NULL DEFAULT 0.850,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_company_channel_date (company_id, channel, snapshot_date),
  KEY idx_snapshot_date (snapshot_date),
  CONSTRAINT fk_hiring_company FOREIGN KEY (company_id) REFERENCES companies(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS company_daily_metrics (
  company_id BIGINT UNSIGNED NOT NULL,
  date DATE NOT NULL,
  open_jobs_total INT NOT NULL,
  open_jobs_7d_delta INT NOT NULL,
  open_jobs_30d_delta INT NOT NULL,
  funding_last_90d_count INT NOT NULL,
  latest_funding_date DATE NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (company_id, date),
  CONSTRAINT fk_metrics_company FOREIGN KEY (company_id) REFERENCES companies(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
