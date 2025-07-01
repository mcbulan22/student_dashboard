import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# === USERS & ROLES ===
users = {
    "admin": {"name": "Sir Marlon", "role": "admin", "password": "adminpass"},
    "faculty": {"name": "Faculty User", "role": "faculty", "password": "facultypass"},
    "m7968": {"name": "MALUYO, AARON JOHN", "role": "student", "password": "aaron123", "midn": "M-7968"},
    "m8142": {"name": "TALISIC, ABDUL NAJIR", "role": "student", "password": "abdul123", "midn": "M-8142"},
    "m7929": {"name": "LALAS, ROMEO JR", "role": "student", "password": "romeo123", "midn": "M-7929"}
}

# === DATA ===
df = pd.read_excel("students.xlsx")

# === SESSION STATE INIT ===
if "login_status" not in st.session_state:
    st.session_state.login_status = False
    st.session_state.username = ""

# === TABS ===
tab1, tab2 = st.tabs(["👤 Individual View (Login)", "👥 Group View"])

# === TAB 1: INDIVIDUAL VIEW (LOGIN REQUIRED) ===
with tab1:
    if not st.session_state.login_status:
        st.subheader("🔑 Login Required to View Student Data")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Login")
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
        with col2:
            st.image("sample_individual_tab.png", caption="Sample of Tab 1 - Individual Student View", use_container_width=True)
    else:
        user_info = users[st.session_state.username]
        role = user_info["role"]
        st.sidebar.title(f"Welcome, {user_info['name']}")
        if st.sidebar.button("Logout"):
            st.session_state.login_status = False
            st.session_state.username = ""
            st.rerun()

        st.subheader("📈 Individual Performance")

        if role == "student":
            student_df = df[df["Midn Number"] == user_info["midn"]]
            st.markdown(f"Showing results for: **{user_info['name']}**")
        else:
            selected_student = st.selectbox("Select a Student", sorted(df["Student Name"].unique()))
            student_df = df[df["Student Name"] == selected_student]

        st.dataframe(student_df)

        # === Line Graph for Continuous Assessment ===
        ca_df = student_df[student_df["Exam"] == "Continuous Assessment"]
        ca_df["Year Level"] = pd.Categorical(ca_df["Year Level"], categories=["First Year", "Second Year", "Third Year"], ordered=True)
        ca_df = ca_df.sort_values("Year Level")

        if not ca_df.empty:
            fig1, ax1 = plt.subplots(figsize=(8, 4))
            sns.lineplot(data=ca_df, x="Year Level", y="Score", marker="o", ax=ax1)
            ax1.set_title("Continuous Assessment Trend")
            ax1.set_ylim(0, 100)
            ax1.set_ylabel("Score (%)")
            plt.tight_layout()
            st.pyplot(fig1)

        # === Radar Chart ===
        radar_df = student_df[student_df["Exam"] == "Continuous Assessment"]
        if not radar_df.empty:
            profile_df = radar_df.groupby("Year Level")["Score"].mean().reindex(["First Year", "Second Year", "Third Year"]).fillna(0)
            categories = profile_df.index.tolist()
            values = profile_df.values.tolist()
            values += values[:1]  # close the circle

            angles = np.linspace(0, 2 * np.pi, len(categories) + 1)

            fig_radar, ax_radar = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
            ax_radar.plot(angles, values, marker='o')
            ax_radar.fill(angles, values, alpha=0.3)
            ax_radar.set_xticks(angles[:-1])
            ax_radar.set_xticklabels(categories)
            ax_radar.set_title("Radar Chart: Yearly Profile")
            st.pyplot(fig_radar)

# === TAB 2: GROUP VIEW ===
with tab2:
    st.subheader("📊 Group Performance")

    # Filters
    program_filter = st.multiselect("Select Program", df["Program"].dropna().unique(), default=list(df["Program"].dropna().unique()))
    exam_filter = st.multiselect("Select Exam Type(s)", df["Exam"].dropna().unique(), default=["COA1", "COA2", "Midterm Exam", "Final Exam"])

    group_df = df[df["Program"].isin(program_filter) & df["Exam"].isin(exam_filter)]

    st.dataframe(group_df)

    if not group_df.empty:
        avg_df = group_df.groupby(["Academic Year", "Course", "Exam"]).mean(numeric_only=True).reset_index()
        avg_df["Academic Year"] = avg_df["Academic Year"].astype(str)

        fig2, ax2 = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=avg_df, x="Academic Year", y="Score", hue="Course", marker="o", ax=ax2)
        ax2.set_title("Average Scores by Course")
        ax2.set_ylabel("Average Score (%)")
        ax2.set_xlabel("Academic Year")
        ax2.legend(title="Course", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        st.pyplot(fig2)

        # Heatmap
        heatmap_data = avg_df.pivot(index="Course", columns="Academic Year", values="Score").fillna(0)
        fig_hm, ax_hm = plt.subplots(figsize=(10, len(heatmap_data) * 0.5))
        sns.heatmap(heatmap_data, annot=True, cmap="YlOrBr", fmt=".0f", linewidths=0.5, ax=ax_hm, cbar_kws={'label': 'Score'})
        ax_hm.set_title("Heatmap of Average Scores by Course")
        st.pyplot(fig_hm)

    # Continuous Assessment Graph (below main filters)
    ca_df = df[df["Exam"] == "Continuous Assessment"]
    ca_df = ca_df[ca_df["Program"].isin(program_filter)]
    ca_df["Year Level"] = pd.Categorical(ca_df["Year Level"], categories=["First Year", "Second Year", "Third Year"], ordered=True)

    if not ca_df.empty:
        st.subheader("📈 Continuous Assessment - Group View")
        ca_avg = ca_df.groupby(["Year Level", "Course"]).mean(numeric_only=True).reset_index()
        fig_ca, ax_ca = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=ca_avg, x="Year Level", y="Score", hue="Course", marker="o", ax=ax_ca)
        ax_ca.set_title("Continuous Assessment by Course and Year")
        ax_ca.set_ylim(0, 100)
        plt.tight_layout()
        st.pyplot(fig_ca)
