from pathlib import Path

import aiosqlite


class Database:
    def __init__(
        self,
        database_path: Path,
        schema_path: Path,
    ) -> None:
        self.database_path = database_path
        self.schema_path = schema_path

    async def initialize(self) -> None:
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        schema = self.schema_path.read_text(encoding="utf-8")

        async with aiosqlite.connect(self.database_path) as connection:
            await connection.execute("PRAGMA foreign_keys = ON;")
            await connection.execute("PRAGMA journal_mode = WAL;")
            await connection.executescript(schema)
            await connection.commit()

    async def connect(self) -> aiosqlite.Connection:
        connection = await aiosqlite.connect(self.database_path)
        connection.row_factory = aiosqlite.Row

        await connection.execute("PRAGMA foreign_keys = ON;")

        return connection
