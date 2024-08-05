import sqlite3


class SqliteService:
    def __init__(self):

        self.db_path = "../record.sqlite3"
        # self.db_path = "F:\\Sensnow\\Code\\Vanna\\record.sqlite3"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.check_table_exists()

    def check_table_exists(self):
        try:
            self.cursor.execute(f"SELECT * FROM `record`")
        except sqlite3.OperationalError:
            create_table_query = f"""
            CREATE TABLE `record` (
                "id" INTEGER NOT NULL,
                "key" TEXT,
                "value" TEXT,
                PRIMARY KEY ("id")
            )
                """
            self.cursor.execute(create_table_query)
            self.conn.commit()

        try:
            self.cursor.execute(f"SELECT * FROM `upload_document`")
        except sqlite3.OperationalError:
            create_table_query = f"""
            CREATE TABLE `upload_document` (
                "id" INTEGER NOT NULL,
                "task_id" INTEGER,
                "state" TEXT,
                "doc" TEXT,
                "doc_state" TEXT,
                "error_message" TEXT,
                PRIMARY KEY ("id")
            )
                """
            self.cursor.execute(create_table_query)
            self.conn.commit()

    def insert_or_update_data(self, data: dict):
        if self.get_column_values('main.record', 'key', data['key']):
            update_query = f"UPDATE main.record SET value={data['value']} WHERE `key`={data['key']}"
            self.cursor.execute(update_query)
        else:
            insert_query = """INSERT INTO "main"."record" ("key", "value") VALUES ('{}', '{}');""".format(
                data['key'], data['value'])
            self.cursor.execute(insert_query)

    def get_column_values(self, table_name, column_name, ch_value=None):
        if ch_value:
            select_query = f"SELECT {column_name} FROM {table_name} WHERE `ID`={ch_value}"
        else:
            select_query = f"SELECT {column_name} FROM {table_name}"
        self.cursor.execute(select_query)
        values = self.cursor.fetchall()
        return values if values else None

    # def create_or_update_column_values(self, table_name, column_name, ch_value, data: dict):
    #     if self.get_column_values(table_name, column_name, ch_value):
    #         update_query = f"UPDATE {table_name} SET {column_name}={data[column_name]} WHERE `ID`={data['ID']}"
    #         self.cursor.execute(update_query)
    #     else:
    #         self.insert_data(table_name, column_name, data)

    def close(self):
        self.conn.close()


if __name__ == '__main__':
    sqlite_service = SqliteService()
    sqlite_service.check_table_exists()
    sqlite_service.close()

