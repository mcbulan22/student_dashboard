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

# === LOGIN LOGIC ===
if "login_status" not in st.session_state:
    st.session_state.login_status = False
    st.session_state.username = ""

if not st.session_state.login_status:
    st.title("📚 MAAP Student Dashboard - Login Required for Tab 1")
    st.markdown("""
    This dashboard provides academic performance data of MAAP students.

    **🔐 Tab 1: Individual View** requires login to protect personal student data. 

    - If you are a **student**, contact CCA to receive **temporary login credentials**.
    - If you are faculty or admin, use your designated credentials.

    _To see what this tab looks like, view the sample below._
    """)
    st.image("sample_individual_tab.png", caption="Sample of Tab 1 - Individual Student View", use_column_width=True)

    st.subheader("🔑 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        if username in users and users[username]["password"] == password:
            st.session_state.login_status = True
            st.session_state.username = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Incorrect username or password.")

else:
    user_info = users[st.session_state.username]
    role = user_info["role"]
    st.sidebar.title(f"Welcome, {user_info['name']}")
    if st.sidebar.button("Logout"):
        st.session_state.login_status = False
        st.session_state.username = ""
        st.rerun()

    # === TABS ===
    tab1, tab2 = st.tabs(["👤 Individual View", "👥 Group View"])

    # === TAB 1: INDIVIDUAL VIEW ===
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

        st.dataframe(student_df)

        if not student_df.empty:
            student_df["Assessment Year"] = student_df["Assessment Year"].astype(int)
            student_df = student_df.sort_values(["Course Name", "Assessment Year"])

            fig1, ax1 = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=student_df, x="Assessment Year", y="Score", hue="Course Name", marker="o", ax=ax1)
            ax1.set_title("Score Trend by Course", fontsize=14)
            ax1.set_ylabel("Score (%)")
            ax1.set_xlabel("Assessment Year")
            ax1.legend(title="Course Name", bbox_to_anchor=(1.05, 1), loc='upper left')
            ax1.set_xticks(sorted(student_df["Assessment Year"].unique()))
            plt.tight_layout()
            st.pyplot(fig1)

    # === TAB 2: GROUP VIEW ===
    with tab2:
        st.subheader("📊 Group Performance Analysis")

        programs = st.multiselect("Select Program(s)", options=df["Program"].unique(), default=list(df["Program"].unique()))
        sponsors = st.multiselect("Select Sponsor(s)", options=df["Sponsor"].unique(), default=list(df["Sponsor"].unique()))

        filtered_df = df[df["Program"].isin(programs) & df["Sponsor"].isin(sponsors)]

        st.dataframe(filtered_df)

        if not filtered_df.empty:
            avg_df = filtered_df.groupby(["Assessment Year", "Course Name"]).mean(numeric_only=True).reset_index()
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
