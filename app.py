import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# --- Login Credentials ---
users = {
    "admin": {"role": "admin", "password": "password"},
    "faculty": {"role": "faculty", "password": "faculty123"},
    "m-7968": {"role": "student", "password": "password", "midn": "M-7968", "name": "MALUYO, AARON JOHN"},
    "m-8142": {"role": "student", "password": "password", "midn": "M-8142", "name": "TALISIC, ABDUL NAJIR"},
    "m-7929": {"role": "student", "password": "password", "midn": "M-7929", "name": "LALAS, ROMEO JR"}
}

# --- Load Data ---
df = pd.read_excel("students.xlsx")
df["Assessment Year"] = df["Assessment Year"].astype(int)

# --- Session State for Login ---
if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.user = None

# --- Tabs ---
tab1, tab2 = st.tabs(["👤 Individual View", "👥 Group View"])

# ===============================
# TAB 1: INDIVIDUAL VIEW (Login Required)
# ===============================
with tab1:
    if not st.session_state.login:
        # Public View (Not Logged In)
        st.title("🔐 Individual Student View - Restricted Access")

        st.subheader("🔑 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.button("Login")  # <-- Moved this line up
        if login_btn:
            if username in users and users[username]["password"] == password:
                st.session_state.login_status = True
                st.session_state.username = username
                st.experimental_rerun()
                st.stop()  # Prevent further code execution after rerun
            else:
                st.error("Incorrect username or password.")

        st.markdown("""
        🚫 **Restricted Access: Individual Student Data**

        This section contains sensitive student performance data and is protected under MAAP’s data privacy guidelines.

        - If you are a **student**, you may request your personal login credentials by contacting the **Center for Competency Assessment (CCA)**.
        - If you are an authorized **faculty or administrator**, please log in below using your assigned credentials.

        _To see what this tab looks like, refer to the sample screenshot below._
        """)

        st.image("sample_individual_tab.png", caption="Sample of Individual Student View", use_container_width=True)


    else:
        # Logged In View
        role = users[st.session_state.user]["role"]
        st.sidebar.success(f"Logged in as {st.session_state.user} ({role})")
        if st.sidebar.button("Logout"):
            st.session_state.login = False
            st.session_state.user = None
            st.experimental_rerun()

        if role == "student":
            midn = users[st.session_state.user]["midn"]
            student_name = users[st.session_state.user]["name"]
            student_df = df[df["Midn Number"] == midn]
        else:
            student_name = st.selectbox("Select a student", sorted(df["Student Name"].unique()))
            student_df = df[df["Student Name"] == student_name]

        st.subheader(f"📈 Academic Profile: {student_name}")
        st.dataframe(student_df)

        if not student_df.empty:
            # Line Chart
            student_df = student_df.sort_values(["Course Name", "Assessment Year"])
            fig1, ax1 = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=student_df, x="Assessment Year", y="Score", hue="Course Name", marker="o", ax=ax1)
            ax1.set_title(f"Score Trend by Course: {student_name}", fontsize=14)
            ax1.set_ylabel("Score (%)")
            ax1.set_xlabel("Assessment Year")
            ax1.legend(title="Course Name", bbox_to_anchor=(1.05, 1), loc='upper left')
            ax1.set_xticks(sorted(student_df["Assessment Year"].unique()))
            st.pyplot(fig1)

            # Radar Chart: Student vs Class Average
            st.subheader("🕸️ Student vs Class Average Profile (Radar)")
            year = st.selectbox("Select Year", sorted(student_df["Assessment Year"].unique()))
            year_df = student_df[student_df["Assessment Year"] == year]

            if not year_df.empty:
                program = year_df["Program"].iloc[0]
                class_df = df[(df["Assessment Year"] == year) & (df["Program"] == program)]
                shared_courses = year_df["Course Name"].unique()
                student_scores = year_df.set_index("Course Name").reindex(shared_courses)["Score"]
                class_avg = class_df.groupby("Course Name")["Score"].mean().reindex(shared_courses)
                radar_df = pd.DataFrame({"Student": student_scores, "ClassAvg": class_avg}).dropna()

                if not radar_df.empty:
                    categories = radar_df.index.tolist()
                    N = len(categories)
                    values_student = radar_df["Student"].tolist() + radar_df["Student"].tolist()[:1]
                    values_class = radar_df["ClassAvg"].tolist() + radar_df["ClassAvg"].tolist()[:1]
                    angles = [n / float(N) * 2 * np.pi for n in range(N)] + [0]

                    fig_radar, ax_radar = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                    ax_radar.plot(angles, values_student, label="Student", linewidth=2)
                    ax_radar.fill(angles, values_student, alpha=0.25)
                    ax_radar.plot(angles, values_class, linestyle="dashed", label="Class Avg", linewidth=2)
                    ax_radar.set_thetagrids(np.degrees(angles[:-1]), categories)
                    ax_radar.set_ylim(0, 100)
                    ax_radar.set_title(f"{student_name}'s Score Profile - {year}", y=1.1)
                    ax_radar.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
                    st.pyplot(fig_radar)
                else:
                    st.warning("No comparable data between student and class for radar chart.")

# ===============================
# TAB 2: GROUP VIEW (Public)
# ===============================
with tab2:
    st.title("📊 Group Performance View (Public)")
    sponsor_filter = st.selectbox("Select Sponsor", sorted(df["Sponsor"].dropna().unique()))
    program_filter = st.selectbox("Select Program", sorted(df["Program"].dropna().unique()))

    group_df = df[(df["Sponsor"] == sponsor_filter) & (df["Program"] == program_filter)]
    st.dataframe(group_df.drop(columns=["Student Name"]))

    if not group_df.empty:
        avg_df = group_df.groupby(["Assessment Year", "Course Name"]).mean(numeric_only=True).reset_index()

        # Line Chart
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=avg_df, x="Assessment Year", y="Score", hue="Course Name", marker="o", ax=ax2)
        ax2.set_title("Average Scores by Course", fontsize=14)
        ax2.set_ylabel("Score (%)")
        ax2.set_xlabel("Assessment Year")
        ax2.legend(title="Course Name", bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.set_xticks(sorted(avg_df["Assessment Year"].unique()))
        st.pyplot(fig2)

        # Heatmap
        st.subheader("🔥 Heatmap of Average Scores")
        pivoted = avg_df.pivot(index="Course Name", columns="Assessment Year", values="Score").fillna(0)
        if not pivoted.empty:
            fig_hm, ax_hm = plt.subplots(figsize=(10, len(pivoted) * 0.5))
            sns.heatmap(pivoted, annot=True, cmap="YlGnBu", fmt=".0f", linewidths=0.5, ax=ax_hm, cbar_kws={'label': 'Score'})
            ax_hm.set_title("Heatmap of Scores", fontsize=14)
            st.pyplot(fig_hm)
        else:
            st.warning("No data to display heatmap.")
