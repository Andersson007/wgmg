CREATE TABLE IF NOT EXISTS w_accounts (
    id BIGINT PRIMARY KEY,
    modifydate TIMESTAMP,
    nickname TEXT,
    created_at BIGINT,
	last_battle_time BIGINT,
	hidden BOOLEAN
    );
CREATE INDEX CONCURRENTLY IF NOT EXISTS w_account_nickname_idx ON w_accounts (nickname);
CREATE INDEX CONCURRENTLY IF NOT EXISTS w_account_created_at_idx ON w_accounts (created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS w_account_last_battle_time_idx ON w_accounts (last_battle_time);

CREATE TABLE IF NOT EXISTS w_statistics (
    id BIGSERIAL PRIMARY KEY,
    acc_id BIGINT UNIQUE,
	modifydate TIMESTAMP,
    xp INT,
	battles INT,
    survived_battles SMALLINT,
    draws SMALLINT,
    frags SMALLINT,
    damage_scouting INT,
    wins SMALLINT,
    damage_dealt INT
    );
ALTER TABLE w_statistics ADD CONSTRAINT w_statistics_acc_id_fk FOREIGN KEY (acc_id) REFERENCES w_accounts(id) ON DELETE CASCADE;
CREATE INDEX CONCURRENTLY IF NOT EXISTS w_statistics_acc_id_idx ON w_statistics (acc_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS w_statistics_battles_idx ON w_statistics (battles);
CREATE INDEX CONCURRENTLY IF NOT EXISTS w_statistics_wins_idx ON w_statistics (wins);
