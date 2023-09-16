import sqlite3
import os


class Poll:
    def __init__(self):
        self._FILE_DB = "poll_db.db"
        if not os.path.isfile(self._FILE_DB):
            with open(self._FILE_DB, "w", encoding="utf-8") as _:
                pass

        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        try:
            c.execute(
                "CREATE TABLE polls (POLL_ID int, MESSAGE_ID str, QUESTION text, OPTIONS list, CORRECT_OPTION int, EXPLANATION str, START_TIME time, END_TIME time, CLOSED bool, PRIMARY KEY (POLL_ID))"
            )
        except sqlite3.OperationalError as exc:
            print(f"Error: {exc}")
        try:
            c.execute(
                "CREATE TABLE players (PLAYER_ID text, name text, score integer, PRIMARY KEY (PLAYER_ID))"
            )
        except sqlite3.OperationalError as exc:
            print(f"Error: {exc}")
        conn.commit()
        conn.close()

        self.update_matches()

    # internal functions

    def close_poll(self, poll_id):
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute("UPDATE polls SET CLOSED = ? WHERE POLL_ID = ?", (True, poll_id))
        conn.commit()
        conn.close()
