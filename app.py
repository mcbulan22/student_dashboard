import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from math import pi

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

# === LOGIN LOGIC ===
if "login_status" not in st.session_state:
    st.session_state.login_status = False
    st.session_state.username = ""

if not st.session_state.login_status:
    tab1, tab2 = st.tabs(["🔐 Login Required", "📊 Group View (Public)"])

    with tab1:
        st.subheader("🔑 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.button("Login")

        if login_btn:
            if username in users and users[username]["password"] == password:
                st.session_state.login_status = True
                st.session_state.username = username
                st.experimental_set_query_params(logged_in="1")
                st.stop()  # Safe halt; streamlit will rerun automatically
            else:
                st.error("Incorrect username or password.")


        st.image("sample_individual_tab.png", caption="Sample of Tab 1 - Individual Student View", use_container_width=True)
        st.markdown("""
        This dashboard provides academic performance data of MAAP students.

        **Tab 1** requires login to protect personal student data.

        - Students may obtain credentials from CCA
        - Faculty/Admin may use institutional logins
        """)

    with tab2:
        st.subheader("📊 Group Performance Analysis")

        programs = st.multiselect("Select Program(s)", options=df["Program"].dropna().unique(), default=list(df["Program"].dropna().unique()))
        sponsors = st.multiselect("Select Sponsor(s)", options=df["Sponsor"].dropna().unique(), default=list(df["Sponsor"].dropna().unique()))

        filtered_df = df[df["Program"].isin(programs) & df["Sponsor"].isin(sponsors)]

        st.dataframe(filtered_df, use_container_width=True)

        if not filtered_df.empty:
            avg_df = filtered_df.groupby(["Assessment Year", "Course Name"], as_index=False).mean(numeric_only=True)
            avg_df["Assessment Year"] = avg_df["Assessment Year"].astype(int)

            fig2, ax2 = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=avg_df, x="Assessment Year", y="Score", hue="Course Name", marker="o", ax=ax2)
            ax2.set_title("Average Scores by Course", fontsize=14)
            ax2.set_ylabel("Average Score (%)")
            ax2.set_xlabel("Assessment Year")
            ax2.legend(title="Course Name", bbox_to_anchor=(1.05, 1), loc='upper left')
            ax2.set_xticks(sorted(avg_df["Assessment Year"].unique()))
            plt.tight_layout()
            st.pyplot(fig2)

            st.subheader("🔥 Heatmap of Average Scores")
            pivoted = avg_df.pivot(index="Course Name", columns="Assessment Year", values="Score").fillna(0)

            if not pivoted.empty:
                fig_hm, ax_hm = plt.subplots(figsize=(10, len(pivoted) * 0.5))
                sns.heatmap(pivoted, annot=True, cmap="YlGnBu", fmt=".0f", linewidths=0.5, ax=ax_hm, cbar_kws={'label': 'Score'})
                ax_hm.set_title("Heatmap of Scores", fontsize=14)
                st.pyplot(fig_hm)
            else:
                st.warning("No data available to generate heatmap.")
        else:
            st.warning("No data matching the selected filters.")

else:
    user_info = users[st.session_state.username]
    role = user_info["role"]
    st.sidebar.title(f"Welcome, {user_info['name']}")
    if st.sidebar.button("Logout"):
        st.session_state.login_status = False
        st.session_state.username = ""
        st.experimental_rerun()

    tab1, tab2 = st.tabs(["👤 Individual View", "👥 Group View"])

    with tab1:
        if role == "student":
            student_df = df[df["Midn Number"] == user_info["midn"]]
            st.subheader(f"📈 Academic Profile: {user_info['name']}")
        elif role in ["admin", "faculty"]:
            st.subheader("Select a Student to View")
            selected_student = st.selectbox("Student Name", sorted(df["Student Name"].unique()))
            student_df = df[df["Student Name"] == selected_student]
        else:
            st.warning("Unauthorized access.")
            st.stop()

        st.dataframe(student_df, use_container_width=True)

        if not student_df.empty:
            student_df = student_df.sort_values(["Course Name", "Assessment Year"])
            student_df["Assessment Year"] = student_df["Assessment Year"].astype(int)

            # === Line Chart ===
            fig1, ax1 = plt.subplots(figsize=(10, 4))
            sns.lineplot(data=student_df, x="Assessment Year", y="Score", hue="Course Name", marker="o", ax=ax1)
            ax1.set_title("Score Trend by Course")
            ax1.set_ylabel("Score (%)")
            ax1.set_xlabel("Assessment Year")
            ax1.legend(title="Course Name", bbox_to_anchor=(1.05, 1), loc='upper left')
            ax1.set_xticks(sorted(student_df["Assessment Year"].unique()))
            st.pyplot(fig1)

            # === Radar Plot ===
            st.subheader("📊 Radar Chart by Year")
            radar_year = st.selectbox("Select Assessment Year", sorted(student_df["Assessment Year"].dropna().unique()))
            student_radar = student_df[student_df["Assessment Year"] == radar_year]

            if not student_radar.empty:
                categories = student_radar["Course Name"].tolist()
                values = student_radar["Score"].tolist()

                class_df = df[(df["Assessment Year"] == radar_year) & (df["Course Name"].isin(categories))]
                class_avg = class_df.groupby("Course Name", as_index=False)["Score"].mean()
                avg_values = class_avg.set_index("Course Name").reindex(categories)["Score"].tolist()

                # Close the radar
                values += values[:1]
                avg_values += avg_values[:1]
                categories += categories[:1]

                angles = [n / float(len(categories)) * 2 * pi for n in range(len(categories))]

                fig3, ax3 = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                ax3.plot(angles, values, label="Student", linewidth=2)
                ax3.fill(angles, values, alpha=0.25)
                ax3.plot(angles, avg_values, label="Class Avg", linestyle="dashed", color="orange")
                ax3.set_xticks(angles[:-1])
                ax3.set_xticklabels(categories[:-1], fontsize=9)
                ax3.set_yticklabels([])
                ax3.set_title(f"Radar Chart: {radar_year}")
                ax3.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
                st.pyplot(fig3)
            else:
                st.warning("No data for selected year.")
