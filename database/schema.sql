PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    guild_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    submitted_by INTEGER NOT NULL,

    source TEXT NOT NULL DEFAULT 'manual'
        CHECK (source IN ('manual', 'integration')),

    experimento TEXT NOT NULL,
    dificuldade TEXT NOT NULL,
    nota TEXT NOT NULL,

    incapacitacoes INTEGER NOT NULL DEFAULT 0
        CHECK (incapacitacoes >= 0),

    morreu INTEGER NOT NULL DEFAULT 0
        CHECK (morreu IN (0, 1)),

    observacao TEXT,

    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (
            status IN (
                'pending',
                'approved',
                'rejected',
                'voided'
            )
        ),

    validation_channel_id INTEGER,
    validation_message_id INTEGER,

    corrected_by INTEGER,
    corrected_at TEXT,

    validated_by INTEGER,
    validated_at TEXT,

    rejection_reason TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_registros_member_status
ON registros (guild_id, member_id, status);

CREATE INDEX IF NOT EXISTS idx_registros_pending
ON registros (guild_id, status);

CREATE TABLE IF NOT EXISTS registro_revisoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    registro_id INTEGER NOT NULL,
    corrected_by INTEGER NOT NULL,

    dados_anteriores TEXT NOT NULL,
    dados_posteriores TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (registro_id)
        REFERENCES registros (id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_revisoes_registro
ON registro_revisoes (registro_id);
