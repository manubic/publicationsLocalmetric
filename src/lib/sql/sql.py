import mysql.connector



class SQL:
    def __init__(self, user: str, host: str, db: str, password: str) -> None:
        self.user = user
        self.host = host
        self.db = db
        self.password = password

    def query(self, query: str) -> list[list[str]] | None:
        conn = mysql.connector.connect(
            user = self.user,
            host = self.host,
            db = self.db,
            password = self.password,
        )
        cursor = conn.cursor()
        cursor.execute(query)
        if cursor.with_rows:
            return [[column for column in row] for row in cursor.fetchall()]     
        conn.commit()

