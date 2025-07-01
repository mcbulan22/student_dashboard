import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# --- AUTHENTICATION SETUP ---
users = {
    "admin": {"role": "admin", "password": "admin123"},
    "faculty": {"role": "faculty", "password": "faculty123"},
    "m-7968": {"role": "student", "password": "pass7968", "midn": "M-7968"},
    "m-8142": {"role": "student", "password": "pass8142", "midn": "M-8142"},
    "m-7929": {"role": "student", "password": "pass7929", "midn": "M-7929"},
}

# --- LOAD DATA ---
df = pd.read_excel("students.xlsx")

# --- LOGIN SYSTEM ---
if "login_status" not in st.session_state:
    st.session_state.login_status = False
    st.session_state.username = ""

st.title("📊 MAAP Student Performance Dashboard - Continuous Assessment of Class 2026")
tab1, tab2 = st.tabs(["👤 Individual View (Login Required)", "👥 Group View"])

# === TAB 1: INDIVIDUAL VIEW ===
with tab1:
    if not st.session_state.login_status:
        st.subheader("🔑 Login")
        username = st.text_input("Username", key="user")
        password = st.text_input("Password", type="password", key="pass")
        login_btn = st.button("Login")

        if login_btn:
            if username in users and users[username]["password"] == password:
                st.session_state.login_status = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Incorrect username or password.")
            # Public View (Not Logged In)
    
    st.title("🔐 Individual Student View - Restricted Access")

        st.markdown("""
        🚫 **Restricted Access: Individual Student Data**

        This section contains sensitive student performance data and is protected under MAAP’s data privacy guidelines.

        - If you are a **student**, you may request your personal login credentials by contacting the **Center for Competency Assessment (CCA)**.
        - If you are an authorized **faculty or administrator**, please log in below using your assigned credentials.

        _To see what this tab looks like, refer to the sample screenshot below._
        """)
    else:
        user = users[st.session_state.username]
        role = user["role"]
        st.sidebar.success(f"Logged in as: {st.session_state.username} ({role})")
        if st.sidebar.button("Logout"):
            st.session_state.login_status = False
            st.session_state.username = ""
            st.rerun()

        if role == "student":
            student_df = df[df["Midn Number"] == user["midn"]]
            student_name = student_df["Student Name"].iloc[0] if not student_df.empty else "Unknown"
            st.subheader(f"📈 Academic Profile: {student_name}")
        elif role in ["admin", "faculty"]:
            st.subheader("Select a Student to View")
            selected_student = st.selectbox("Student Name", sorted(df["Student Name"].unique()))
            student_df = df[df["Student Name"] == selected_student]
            student_name = selected_student
        else:
            st.warning("Unauthorized role.")
            st.stop()

        st.dataframe(student_df)

        if not student_df.empty:
            student_df["Assessment Year"] = student_df["Assessment Year"].astype(int)
            student_df = student_df.sort_values(["Course Name", "Assessment Year"])

            fig1, ax1 = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=student_df, x="Assessment Year", y="Score", hue="Course Name", marker="o", ax=ax1)
            ax1.set_title(f"Score Trend by Course: {student_name}", fontsize=14)
            ax1.set_ylabel("Score (%)")
            ax1.set_xlabel("Assessment Year")
            ax1.legend(title="Course Name", bbox_to_anchor=(1.05, 1), loc='upper left')
            ax1.set_xticks(sorted(student_df["Assessment Year"].unique()))
            plt.tight_layout()
            st.pyplot(fig1)

            # === RADAR CHART ===
            st.subheader("🕸️ Student vs Class Average Profile (Radar)")
            year = st.selectbox("Select Year", sorted(student_df["Assessment Year"].unique()))
            year_student = student_df[student_df["Assessment Year"] == year]

            if not year_student.empty:
                program_name = year_student["Program"].iloc[0]
                year_program = df[(df["Assessment Year"] == year) & (df["Program"] == program_name)]
                shared_courses = year_student["Course Name"].unique()
                student_scores = year_student.set_index("Course Name").reindex(shared_courses)["Score"]
                class_avg_scores = year_program.groupby("Course Name")["Score"].mean().reindex(shared_courses)

                combined = pd.DataFrame({
                    "Student": student_scores,
                    "ClassAvg": class_avg_scores
                }).dropna()

                if not combined.empty:
                    categories = combined.index.tolist()
                    N = len(categories)
                    values_student = combined["Student"].tolist()
                    values_class = combined["ClassAvg"].tolist()
                    values_student += values_student[:1]
                    values_class += values_class[:1]
                    angles = [n / float(N) * 2 * np.pi for n in range(N)]
                    angles += angles[:1]

                    fig_radar, ax_radar = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                    ax_radar.plot(angles, values_student, linewidth=2, label="Student")
                    ax_radar.fill(angles, values_student, alpha=0.25)
                    ax_radar.plot(angles, values_class, linewidth=2, linestyle='dashed', label="Class Avg")
                    ax_radar.set_thetagrids(np.degrees(angles[:-1]), categories)
                    ax_radar.set_title(f"{student_name}'s Score Profile - {year}", y=1.1)
                    ax_radar.set_ylim(0, 100)
                    ax_radar.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
                    st.pyplot(fig_radar)
                else:
                    st.warning("No comparable data between student and group for that year.")

# === TAB 2: GROUP VIEW ===
with tab2:
    st.subheader("Group Performance Analysis")
    program = st.selectbox("Select Program", sorted(df["Program"].unique()))
    sponsor = st.selectbox("Select Sponsor", sorted(df["Sponsor"].unique()))

    group_df = df[(df["Program"] == program) & (df["Sponsor"] == sponsor)]
    st.dataframe(group_df)

    if not group_df.empty:
        avg_df = group_df.groupby(["Assessment Year", "Course Name"]).mean(numeric_only=True).reset_index()
        avg_df["Assessment Year"] = avg_df["Assessment Year"].astype(int)
        avg_df = avg_df.sort_values(["Course Name", "Assessment Year"])

        fig2, ax2 = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=avg_df, x="Assessment Year", y="Score", hue="Course Name", marker="o", ax=ax2)
        ax2.set_title(f"Average Scores by Course - {program} ({sponsor})", fontsize=14)
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
            ax_hm.set_title(f"Heatmap - {program} ({sponsor})", fontsize=14)
            st.pyplot(fig_hm)
        else:
            st.warning("No data available to generate heatmap for this program.")
