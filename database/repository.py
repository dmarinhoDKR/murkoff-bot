import json
from typing import Any

from database.connection import Database


class RegistroRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def criar(
        self,
        *,
        guild_id: int,
        member_id: int,
        submitted_by: int,
        source: str,
        experimento: str,
        dificuldade: str,
        nota: str,
        incapacitacoes: int,
        morreu: bool,
        observacao: str | None,
    ) -> int:
        connection = await self.database.connect()

        try:
            cursor = await connection.execute(
                """
                INSERT INTO registros (
                    guild_id,
                    member_id,
                    submitted_by,
                    source,
                    experimento,
                    dificuldade,
                    nota,
                    incapacitacoes,
                    morreu,
                    observacao,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                """,
                (
                    guild_id,
                    member_id,
                    submitted_by,
                    source,
                    experimento.strip(),
                    dificuldade.strip(),
                    nota.strip(),
                    incapacitacoes,
                    int(morreu),
                    observacao.strip() if observacao else None,
                ),
            )

            await connection.commit()

            if cursor.lastrowid is None:
                raise RuntimeError("O banco não retornou o ID do registro.")

            return cursor.lastrowid
        finally:
            await connection.close()

    async def buscar(
        self,
        registro_id: int,
        guild_id: int,
    ) -> dict[str, Any] | None:
        connection = await self.database.connect()

        try:
            cursor = await connection.execute(
                """
                SELECT *
                FROM registros
                WHERE id = ?
                  AND guild_id = ?
                """,
                (
                    registro_id,
                    guild_id,
                ),
            )

            row = await cursor.fetchone()

            if row is None:
                return None

            return dict(row)
        finally:
            await connection.close()

    async def salvar_mensagem_validacao(
        self,
        *,
        registro_id: int,
        guild_id: int,
        channel_id: int,
        message_id: int,
    ) -> bool:
        connection = await self.database.connect()

        try:
            cursor = await connection.execute(
                """
                UPDATE registros
                SET validation_channel_id = ?,
                    validation_message_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND guild_id = ?
                  AND status = 'pending'
                """,
                (
                    channel_id,
                    message_id,
                    registro_id,
                    guild_id,
                ),
            )

            await connection.commit()

            return cursor.rowcount == 1
        finally:
            await connection.close()

    async def listar_pendentes(
        self,
        guild_id: int,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        connection = await self.database.connect()

        try:
            cursor = await connection.execute(
                """
                SELECT *
                FROM registros
                WHERE guild_id = ?
                  AND status = 'pending'
                ORDER BY created_at ASC, id ASC
                LIMIT ?
                """,
                (
                    guild_id,
                    limit,
                ),
            )

            rows = await cursor.fetchall()

            return [dict(row) for row in rows]
        finally:
            await connection.close()

    async def aprovar(
        self,
        *,
        registro_id: int,
        guild_id: int,
        validated_by: int,
    ) -> bool:
        connection = await self.database.connect()

        try:
            cursor = await connection.execute(
                """
                UPDATE registros
                SET status = 'approved',
                    validated_by = ?,
                    validated_at = CURRENT_TIMESTAMP,
                    rejection_reason = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND guild_id = ?
                  AND status = 'pending'
                """,
                (
                    validated_by,
                    registro_id,
                    guild_id,
                ),
            )

            await connection.commit()

            return cursor.rowcount == 1
        finally:
            await connection.close()

    async def rejeitar(
        self,
        *,
        registro_id: int,
        guild_id: int,
        validated_by: int,
        reason: str,
    ) -> bool:
        connection = await self.database.connect()

        try:
            cursor = await connection.execute(
                """
                UPDATE registros
                SET status = 'rejected',
                    validated_by = ?,
                    validated_at = CURRENT_TIMESTAMP,
                    rejection_reason = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND guild_id = ?
                  AND status = 'pending'
                """,
                (
                    validated_by,
                    reason.strip(),
                    registro_id,
                    guild_id,
                ),
            )

            await connection.commit()

            return cursor.rowcount == 1
        finally:
            await connection.close()

    async def corrigir(
        self,
        *,
        registro_id: int,
        guild_id: int,
        corrected_by: int,
        experimento: str,
        dificuldade: str,
        nota: str,
        incapacitacoes: int,
        morreu: bool,
    ) -> bool:
        connection = await self.database.connect()

        try:
            await connection.execute("BEGIN IMMEDIATE")

            cursor = await connection.execute(
                """
                SELECT
                    experimento,
                    dificuldade,
                    nota,
                    incapacitacoes,
                    morreu
                FROM registros
                WHERE id = ?
                  AND guild_id = ?
                  AND status = 'pending'
                """,
                (
                    registro_id,
                    guild_id,
                ),
            )

            row = await cursor.fetchone()

            if row is None:
                await connection.rollback()
                return False

            dados_anteriores = {
                "experimento": row["experimento"],
                "dificuldade": row["dificuldade"],
                "nota": row["nota"],
                "incapacitacoes": row["incapacitacoes"],
                "morreu": bool(row["morreu"]),
            }

            dados_posteriores = {
                "experimento": experimento.strip(),
                "dificuldade": dificuldade.strip(),
                "nota": nota.strip(),
                "incapacitacoes": incapacitacoes,
                "morreu": morreu,
            }

            await connection.execute(
                """
                INSERT INTO registro_revisoes (
                    registro_id,
                    corrected_by,
                    dados_anteriores,
                    dados_posteriores
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    registro_id,
                    corrected_by,
                    json.dumps(
                        dados_anteriores,
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        dados_posteriores,
                        ensure_ascii=False,
                    ),
                ),
            )

            update_cursor = await connection.execute(
                """
                UPDATE registros
                SET experimento = ?,
                    dificuldade = ?,
                    nota = ?,
                    incapacitacoes = ?,
                    morreu = ?,
                    corrected_by = ?,
                    corrected_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND guild_id = ?
                  AND status = 'pending'
                """,
                (
                    experimento.strip(),
                    dificuldade.strip(),
                    nota.strip(),
                    incapacitacoes,
                    int(morreu),
                    corrected_by,
                    registro_id,
                    guild_id,
                ),
            )

            if update_cursor.rowcount != 1:
                await connection.rollback()
                return False

            await connection.commit()
            return True
        except Exception:
            await connection.rollback()
            raise
        finally:
            await connection.close()
