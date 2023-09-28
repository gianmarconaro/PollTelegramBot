import sqlite3
import os


class Poll:
    def __init__(self):
        self._FILE_DB = "db/poll_db.db"
        if not os.path.isfile(self._FILE_DB):
            with open(self._FILE_DB, "w", encoding="utf-8") as _:
                pass

        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        try:
            c.execute(
                "CREATE TABLE IF NOT EXISTS polls (POLL_ID int, TELEGRAM_POLL_ID int, MESSAGE_ID str, QUESTION text, OPTIONS list, CORRECT_OPTION int, EXPLANATION str, START_TIME time, END_TIME time, CLOSED bool, PRIMARY KEY (POLL_ID))"
            )
        except sqlite3.OperationalError as exc:
            print(f"Error: {exc}")
        try:
            c.execute(
                "CREATE TABLE IF NOT EXISTS players (TELEGRAM_PLAYER_ID text, USERNAME text, SCORE int, STREAK int, LONGEST_STREAK int, PRIMARY KEY (TELEGRAM_PLAYER_ID))"
            )
        except sqlite3.OperationalError as exc:
            print(f"Error: {exc}")
        try:
            c.execute(
                "CREATE TABLE IF NOT EXISTS votes (TELEGRAM_PLAYER_ID text, TELEGRAM_POLL_ID int, CORRECT bool, PRIMARY KEY (TELEGRAM_PLAYER_ID, TELEGRAM_POLL_ID))"
            )
        except sqlite3.OperationalError as exc:
            print(f"Error: {exc}")
        conn.commit()
        conn.close()

    # internal functions

    def add_poll(
        self,
        poll_id,
        telegram_poll_id,
        message_id,
        question,
        options,
        correct_option,
        explanation,
        start_time,
        end_time,
    ):
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute(
            "INSERT INTO polls VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                poll_id,
                telegram_poll_id,
                message_id,
                question,
                options,
                correct_option,
                explanation,
                start_time,
                end_time,
                False,
            ),
        )
        conn.commit()
        conn.close()

    def close_poll(self, poll_id):
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute("UPDATE polls SET CLOSED = ? WHERE POLL_ID = ?", (True, poll_id))
        conn.commit()
        conn.close()

    def get_next_poll_id(self):
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute("SELECT MAX(POLL_ID) FROM polls")
        poll_id = c.fetchone()[0]
        conn.close()
        return poll_id + 1 if poll_id else 1

    def get_poll(self, telegram_poll_id):
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute("SELECT * FROM polls WHERE TELEGRAM_POLL_ID = ?", (telegram_poll_id,))
        poll = c.fetchone()
        conn.close()
        return poll

    def get_open_polls(self):
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute("SELECT * FROM polls WHERE CLOSED = ?", (False,))
        polls = c.fetchall()
        conn.close()
        return polls

    def increment_score_player(self, telegram_player_id):
        # increment score and streak and check if longest_streak is beaten
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute(
            "SELECT * FROM players WHERE TELEGRAM_PLAYER_ID = ?", (telegram_player_id,)
        )
        player = c.fetchone()
        score = player[2] + 1
        streak = player[3] + 1
        longest_streak = player[4]
        if streak > longest_streak:
            longest_streak = streak
        c.execute(
            "UPDATE players SET score = ?, streak = ?, longest_streak = ? WHERE TELEGRAM_PLAYER_ID = ?",
            (score, streak, longest_streak, telegram_player_id),
        )
        conn.commit()

    def reset_streak_player(self, telegram_player_id):
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute(
            "UPDATE players SET streak = 0 WHERE TELEGRAM_PLAYER_ID = ?",
            (telegram_player_id,),
        )
        conn.commit()
        conn.close()

    def add_player(self, telegram_player_id, username):
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute(
            "SELECT * FROM players WHERE TELEGRAM_PLAYER_ID = ?", (telegram_player_id,)
        )
        player = c.fetchone()
        if not player:
            c.execute(
                "INSERT INTO players VALUES (?, ?, ?, ?, ?)",
                (telegram_player_id, username, 0, 0, 0),
            )
            conn.commit()
        conn.close()

    def get_scoreboard(self):
        # order by score desc and streak desc
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute("SELECT * FROM players ORDER BY score DESC, longest_streak DESC, streak DESC")
        scoreboard = c.fetchall()
        conn.close()
        return scoreboard

    def save_vote(self, telegram_player_id, telegram_poll_id, correct):
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute(
            "INSERT INTO votes VALUES (?, ?, ?)",
            (telegram_player_id, telegram_poll_id, correct),
        )
        conn.commit()
        conn.close()

    def get_telegram_poll_id_from_poll_id(self, poll_id):
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute("SELECT TELEGRAM_POLL_ID FROM polls WHERE POLL_ID = ?", (poll_id,))
        telegram_poll_id = c.fetchone()[0]
        conn.close()
        return telegram_poll_id

    def get_votes(self, poll_id):
        telegram_poll_id = self.get_telegram_poll_id_from_poll_id(poll_id)

        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute("SELECT * FROM votes WHERE TELEGRAM_POLL_ID = ?", (telegram_poll_id,))
        votes = c.fetchall()
        conn.close()
        return votes

    def get_poll_status(self, poll_id):
        # use the poll_id and not the telegram_poll_id
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute("SELECT CLOSED FROM polls WHERE POLL_ID = ?", (poll_id,))
        poll = c.fetchone()[0]
        conn.close()
        return poll

    def update_scores(self, poll_id):
        # check thta poll is closed
        poll = self.get_poll_status(poll_id)
        if poll:
            votes = self.get_votes(poll_id)
            for vote in votes:
                telegram_player_id, correct = vote[0], vote[2]
                if correct:
                    self.increment_score_player(telegram_player_id)
                else:
                    self.reset_streak_player(telegram_player_id)

    def get_votes_poll_if_closed(self):
        # select all votes from votes and check if poll is closed
        conn = sqlite3.connect(self._FILE_DB)
        c = conn.cursor()
        c.execute("SELECT polls.POLL_ID, players.USERNAME, votes.CORRECT FROM votes INNER JOIN players ON votes.TELEGRAM_PLAYER_ID = players.TELEGRAM_PLAYER_ID INNER JOIN polls ON votes.TELEGRAM_POLL_ID = polls.TELEGRAM_POLL_ID WHERE polls.CLOSED = ?", (False,))
        votes = c.fetchall()
        conn.close()
        return votes