import asyncio
from app.database.mysqldb_mod import get_mesql
from sqlalchemy import text

async def show_tables():
    async with get_mesql() as client:
        result = await client.execute(text("SHOW TABLES;"))
        tables = result.fetchall()
        if tables:
            print("Таблиці у базі даних:")
            for table in tables:
                # Припускаємо, що кожен рядок – це кортеж з назвою таблиці
                print(table[0])
        else:
            print("База даних порожня: жодної таблиці не знайдено.")

# if __name__ == "__main__":
#     asyncio.run(show_tables())
