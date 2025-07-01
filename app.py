import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Sample users and credentials
users = {
    "admin": {"role": "admin", "password": "admin123"},
    "faculty": {"role": "faculty", "password": "faculty123"},
    "m7968": {"role": "student", "password": "pass7968", "midn": "M-7968"},
    "m8142": {"role": "student", "password": "pass8142", "midn": "M-8142"},
    "m7929": {"role": "student", "password": "pass7929", "midn": "M-7929"},
}

# Load data from Excel or define sample data
sample_data = pd.DataFrame({
    "Student Name": ["MALUYO, AARON JOHN", "TALISIC, ABDUL NAJIR", "LALAS, ROMEO JR"],
    "Exam": ["First Year - Engine - E Mat", "First Year - Deck - D Watch 1", "First Year - Engine - E Mat"],
    "Score": [100, 95, 100],
    "Program": ["Engine", "Deck", "Engine"],
    "Year Level": ["First Year", "First Year", "First Year"],
    "Assessment Year": [2023, 2023, 2023],
    "Course Name": ["E Mat", "D Watch 1", "E Mat"],
    "Sponsor": ["IMMAJ", "IMEC", "OTHERS"],
    "Midn Number": ["M-7968", "M-8142", "M-7929"]
})

# App layout
st.set_page_config(page_title="MAAP Student Dashboard", layout="wide")
st.title("📊 MAAP Student Performance Dashboard")

tab1, tab2 = st.tabs(["👤 Individual View", "👥 Group View"])

# --- INDIVIDUAL TAB ---
with tab1:
    st.subheader("Individual Student Analysis (Login Required)")
    with st.container():
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.button("Login")

    if username and password:
        user = users.get(username)
        if user and user["password"] == password:
            st.success(f"Welcome {username}!")
            role = user["role"]

            if role == "admin" or role == "faculty":
                student_df = sample_data.copy()
            elif role == "student":
                student_df = sample_data[sample_data["Midn Number"] == user["midn"]]
            else:
                student_df = pd.DataFrame()

            if not student_df.empty:
                st.dataframe(student_df)

                # Line Chart
                fig1, ax1 = plt.subplots(figsize=(10, 5))
                sns.lineplot(data=student_df, x="Assessment Year", y="Score", hue="Course Name", marker="o", ax=ax1)
                ax1.set_title("Score Trend by Course")
                ax1.set_ylabel("Score (%)")
                ax1.set_xlabel("Assessment Year")
                st.pyplot(fig1)

                # Radar Chart: Only if student has data for one year
                year = st.selectbox("Select Year for Radar Chart", sorted(student_df["Assessment Year"].unique()))
                year_data = student_df[student_df["Assessment Year"] == year]
                if not year_data.empty:
                    courses = year_data["Course Name"].tolist()
                    scores = year_data["Score"].tolist()

                    if len(courses) >= 2:
                        scores += scores[:1]
                        angles = [n / float(len(courses)) * 2 * np.pi for n in range(len(courses))] + [0]

                        fig2, ax2 = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                        ax2.plot(angles, scores, linewidth=2)
                        ax2.fill(angles, scores, alpha=0.25)
                        ax2.set_thetagrids(np.degrees(angles[:-1]), courses)
                        ax2.set_title("Student Radar Profile")
                        st.pyplot(fig2)
                    else:
                        st.warning("Not enough courses to plot radar chart.")
                else:
                    st.warning("No data for selected year.")
            else:
                st.warning("No data found for user.")
        else:
            st.error("Incorrect username or password.")
    else:
        st.info("Since this tab will show data of specific student(s), it requires login credentials to ensure access is limited to authorized individuals.\n\nIf you need to see data of all or group of students, please contact the CCA first, sign relevant data privacy documents, and request login credentials (valid for a day or specified period).\n\nIf you're a student and want to view your academic profile, please coordinate with the CCA to get a temporary login credential that expires after a given time.")
        st.markdown("**To see what this tab looks like, view the sample below:**")
        st.image("sample_individual_tab.png", use_container_width=True)

# --- GROUP TAB ---
with tab2:
    st.subheader("Group Performance Analysis")
    programs = st.multiselect("Select Program(s)", sorted(sample_data["Program"].unique()), default=sorted(sample_data["Program"].unique()))
    sponsors = st.multiselect("Select Sponsor(s)", sorted(sample_data["Sponsor"].unique()), default=sorted(sample_data["Sponsor"].unique()))

    filtered_df = sample_data[(sample_data["Program"].isin(programs)) & (sample_data["Sponsor"].isin(sponsors))]

    if not filtered_df.empty:
        avg_df = filtered_df.groupby(["Assessment Year", "Course Name"], as_index=False).mean(numeric_only=True)
        st.dataframe(avg_df)

        # Line Chart
        fig3, ax3 = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=avg_df, x="Assessment Year", y="Score", hue="Course Name", marker="o", ax=ax3)
        ax3.set_title("Average Scores by Course")
        ax3.set_ylabel("Average Score (%)")
        ax3.set_xlabel("Assessment Year")
        st.pyplot(fig3)

        # Heatmap
        st.subheader("Heatmap of Average Scores")
        heatmap_data = avg_df.pivot(index="Course Name", columns="Assessment Year", values="Score").fillna(0)
        fig4, ax4 = plt.subplots(figsize=(10, len(heatmap_data) * 0.5))
        sns.heatmap(heatmap_data, annot=True, cmap="YlGnBu", fmt=".0f", linewidths=0.5, ax=ax4, cbar_kws={'label': 'Score'})
        ax4.set_title("Score Heatmap")
        st.pyplot(fig4)
    else:
        st.warning("No data for selected filters.")
