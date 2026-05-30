import streamlit as st  # type: ignore
import sqlite3
from datetime import datetime
import pandas as pd  # type: ignore
import matplotlib.pyplot as plt  # type: ignore


# ----------------------------
# DATABASE SETUP
# ----------------------------

def create_table():
    conn = sqlite3.connect("memory.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT,
        score INTEGER,
        total INTEGER,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()


# ----------------------------
# SAVE SCORE
# ----------------------------

def save_score(topic, score, total):

    conn = sqlite3.connect("memory.db")
    c = conn.cursor()

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
    INSERT INTO scores(topic, score, total, date)
    VALUES (?, ?, ?, ?)
    """, (topic, score, total, date))

    conn.commit()
    conn.close()


# ----------------------------
# GET SCORES
# ----------------------------

def get_scores(topic):

    conn = sqlite3.connect("memory.db")
    c = conn.cursor()

    c.execute("""
    SELECT score, total, date
    FROM scores
    WHERE topic = ?
    ORDER BY date DESC
    """, (topic,))

    records = c.fetchall()

    conn.close()

    return records


# ----------------------------
# MEMORY DRIFT
# ----------------------------

def calculate_drift(topic):

    conn = sqlite3.connect("memory.db")
    c = conn.cursor()

    c.execute("""
    SELECT score
    FROM scores
    WHERE topic = ?
    ORDER BY date ASC
    """, (topic,))

    records = c.fetchall()

    conn.close()

    if len(records) < 2:
        return None

    initial_score = records[0][0]
    latest_score = records[-1][0]

    if initial_score == 0:
        return 0

    drift = ((initial_score - latest_score) / initial_score) * 100

    return round(drift, 2)


# ----------------------------
# GRAPH
# ----------------------------

def plot_scores(topic):

    conn = sqlite3.connect("memory.db")

    query = """
    SELECT score, date
    FROM scores
    WHERE topic = ?
    ORDER BY date
    """

    df = pd.read_sql_query(query, conn, params=(topic,))

    conn.close()

    if len(df) > 0:

        fig, ax = plt.subplots()

        ax.plot(
            df["date"],
            df["score"],
            marker="o"
        )

        ax.set_title(f"{topic} Score History")
        ax.set_xlabel("Date")
        ax.set_ylabel("Score")

        plt.xticks(rotation=45)

        st.pyplot(fig)


# ----------------------------
# TOPIC DASHBOARD
# ----------------------------

def topic_dashboard():

    conn = sqlite3.connect("memory.db")

    query = """
    SELECT DISTINCT topic
    FROM scores
    """

    topics = pd.read_sql_query(query, conn)

    dashboard_data = []

    for topic in topics["topic"]:

        topic_scores = pd.read_sql_query(
            """
            SELECT score
            FROM scores
            WHERE topic = ?
            ORDER BY date ASC
            """,
            conn,
            params=(topic,)
        )

        attempts = len(topic_scores)

        if attempts >= 1:

            initial_score = topic_scores.iloc[0]["score"]
            latest_score = topic_scores.iloc[-1]["score"]

            if attempts > 1 and initial_score != 0:

                drift = round(
                    ((initial_score - latest_score) /
                     initial_score) * 100,
                    2
                )

            else:
                drift = 0

            retention = 100 - drift

            dashboard_data.append([
                topic,
                attempts,
                latest_score,
                drift,
                retention
            ])

    conn.close()

    df = pd.DataFrame(
        dashboard_data,
        columns=[
            "Topic",
            "Attempts",
            "Latest Score",
            "Drift %",
            "Retention %"
        ]
    )

    st.subheader("📊 Topic-wise Dashboard")
    st.dataframe(df)


# ----------------------------
# MAIN APP
# ----------------------------

def main():

    create_table()

    st.title("🧠 Memory Drift Detector")

    topic = st.text_input(
        "Enter Topic"
    ).strip().upper()

    score = st.number_input(
        "Score",
        min_value=0,
        step=1
    )

    total = st.number_input(
        "Total Marks",
        min_value=1,
        step=1
    )

    # SAVE SCORE

    if st.button("Submit Quiz"):

        if topic == "":
            st.warning("Enter Topic Name")

        else:

            save_score(topic, score, total)

            st.success(
                "Score Saved Successfully!"
            )

    # SHOW PROGRESS

    if st.button("Show Progress"):

        if topic == "":
            st.warning("Enter Topic Name")

        else:

            records = get_scores(topic)

            if len(records) == 0:

                st.warning("No Records Found")

            else:

                st.subheader("Progress History")

                for r in records:

                    st.write(
                        f"Score: {r[0]}/{r[1]} | Date: {r[2]}"
                    )

    # CALCULATE DRIFT

    if st.button("Calculate Memory Drift"):

        if topic == "":
            st.warning("Enter Topic Name")

        else:

            drift = calculate_drift(topic)

            if drift is None:

                st.warning(
                    "Need At Least 2 Attempts"
                )

            else:

                st.subheader(
                    f"Memory Drift: {drift}%"
                )

                retention = 100 - drift

                st.subheader(
                    f"Retention Score: {retention}%"
                )

                if drift < 10:

                    st.success(
                        "Excellent Retention"
                    )

                elif drift < 30:

                    st.info(
                        "Moderate Forgetting"
                    )

                else:

                    st.error(
                        "Revision Recommended"
                    )

                plot_scores(topic)

    # TOPIC DASHBOARD

    if st.button("Show Topic Dashboard"):
        topic_dashboard()


if __name__ == "__main__":
    main()

