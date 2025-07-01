import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# === MANUAL LOGIN SYSTEM ===
users = {
    "admin": {"name": "Sir Marlon", "role": "admin", "password": "adminpass"},
    "faculty": {"name": "Faculty User", "role": "faculty", "password": "facultypass"},
    "m7968": {"name": "MALUYO, AARON JOHN", "role": "student", "password": "aaron123", "midn": "M-7968"},
    "m8142": {"name": "TALISIC, ABDUL NAJIR", "role": "student", "password": "abdul123", "midn": "M-8142"},
    "m7929": {"name": "LALAS, ROMEO JR", "role": "student", "password": "romeo123", "midn": "M-7929"}
}

# === LOAD DATA ===
df = pd.read_excel("students.xlsx")
df["Assessment Year"] = pd.to_numeric(df["Assessment Year"], errors="coerce").astype("Int64")

# === LOGIN LOGIC ===
if "login_status" not in st.session_state:
    st.session_state.login_status = False
    st.session_state.username = ""

st.set_page_config(page_title="MAAP Student Dashboard", layout="wide")
tab1, tab2 = st.tabs(["🔐 Individual View (Login Required)", "📊 Group View"])

# === TAB 1: LOGIN-BASED INDIVIDUAL VIEW ===
with tab1:
    if not st.session_state.login_status:
        with st.container():
            left, right = st.columns([1, 2])
            with left:
                st.subheader("Login")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.button("Login"):
                    if username in users and users[username]["password"] == password:
                        st.session_state.login_status = True
                        st.session_state.username = username
                        st.experimental_rerun()
                    else:
                        st.error("Incorrect username or password.")
            with right:
                st.markdown("""
                #### About This Dashboard
                This section is only accessible by logged-in users.
                
                - **Students**: View your personal academic record
                - **Faculty/Admin**: Access records of all students
                """)
                st.image("sample_individual_tab.png", caption="Sample View", use_container_width=True)

    else:
        user = users[st.session_state.username]
        role = user["role"]
        st.sidebar.success(f"Welcome, {user['name']}")
        if st.sidebar.button("Logout"):
            st.session_state.login_status = False
            st.session_state.username = ""
            st.experimental_rerun()

        st.subheader("📈 Academic Profile")
        if role == "student":
            student_df = df[df["Midn Number"] == user["midn"]]
        else:
            selected_name = st.selectbox("Select Student", sorted(df["Student Name"].unique()))
            student_df = df[df["Student Name"] == selected_name]

        st.dataframe(student_df)

        if not student_df.empty:
            # Line chart: Score trend by Course over the years
            exam_filter_values = student_df["Exam"].dropna().unique().tolist()
            default_exams = [e for e in ["COA1", "COA2", "Midterm Exam", "Final Exam"] if e in exam_filter_values]
            exam_filter = st.multiselect("Select Exam Type(s)", exam_filter_values, default=default_exams)

            exam_df = student_df[student_df["Exam"].isin(exam_filter)]
            if not exam_df.empty:
                fig1, ax1 = plt.subplots(figsize=(10, 5))
                sns.lineplot(data=exam_df, x="Assessment Year", y="Score", hue="Course Name", marker="o", ax=ax1)
                ax1.set_title("Score Trends by Course")
                ax1.set_xticks(sorted(exam_df["Assessment Year"].dropna().unique()))
                ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                st.pyplot(fig1)

            # Radar Plot (average by year level)
            radar_df = student_df[student_df["Exam"] == "Continuous Assessment"]
            if not radar_df.empty:
                avg_radar = radar_df.groupby("Year Level")["Score"].mean().reindex(["First Year", "Second Year", "Third Year"]).fillna(0)
                categories = avg_radar.index.tolist()
                values = avg_radar.values.tolist()
                values += values[:1]  # close the radar

                fig2, ax2 = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
                angles += angles[:1]

                ax2.plot(angles, values, marker='o')
                ax2.fill(angles, values, alpha=0.3)
                ax2.set_thetagrids(np.degrees(angles[:-1]), categories)
                ax2.set_title("Continuous Assessment Profile by Year Level")
                st.pyplot(fig2)

# === TAB 2: GROUP VIEW ===
with tab2:
    st.subheader("📊 Group Performance")
    programs = st.multiselect("Select Program(s)", options=df["Program"].dropna().unique(), default=list(df["Program"].dropna().unique()))
    sponsors = st.multiselect("Select Sponsor(s)", options=df["Sponsor"].dropna().unique(), default=list(df["Sponsor"].dropna().unique()))

    filtered_df = df[df["Program"].isin(programs) & df["Sponsor"].isin(sponsors)]
    st.dataframe(filtered_df)

    if not filtered_df.empty:
        # Line graph
        avg_df = filtered_df.groupby(["Assessment Year", "Course Name"])["Score"].mean().reset_index()
        fig3, ax3 = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=avg_df, x="Assessment Year", y="Score", hue="Course Name", marker="o", ax=ax3)
        ax3.set_title("Average Scores by Course")
        ax3.set_xticks(sorted(avg_df["Assessment Year"].dropna().unique()))
        ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        st.pyplot(fig3)

        # Heatmap
        pivoted = avg_df.pivot(index="Course Name", columns="Assessment Year", values="Score").fillna(0)
        fig4, ax4 = plt.subplots(figsize=(10, len(pivoted) * 0.5))
        sns.heatmap(pivoted, annot=True, cmap="YlGnBu", fmt=".0f", linewidths=0.5, ax=ax4, cbar_kws={'label': 'Score'})
        ax4.set_title("Heatmap of Average Scores")
        st.pyplot(fig4)
