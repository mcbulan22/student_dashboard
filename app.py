
import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Authentication setup
credentials = {
    "usernames": {
        "Admin": {
            "email": "marlon.bulan@maap.edu.ph",
            "name": "Sir Marlon",
            "password": "$2b$12$I4J0sbdaLJCl2TzHi.j3JO55W2AFz3M/RxZUpHu9xsa05cn6Ad.bm"
        }
    }
}
authenticator = stauth.Authenticate(credentials, "maap_cookie", "maap_secret", 1)
name, auth_status, username = authenticator.login("Login", location="main")

if auth_status:
    st.sidebar.image("maap_logo.png", width=120)
    st.sidebar.title(f"Welcome, {name}")
    authenticator.logout("Logout", "sidebar")

    df = pd.read_excel("students.xlsx")
    df["Academic Year"] = df["Academic Year"].astype(str)
    df["Score"] = df["Score"].astype(float)

    st.title("📊 MAAP Exam Performance Dashboard")
    tab1, tab2 = st.tabs(["👤 Individual View", "👥 Group View"])

    with tab1:
        st.header("Individual Performance")
        student = st.selectbox("Select Student", sorted(df["Student Name"].unique()))
        year_level_group = st.multiselect(
    "Year Level",
    sorted(df["Year Level"].dropna().unique()),
    default=sorted(df["Year Level"].dropna().unique()),
    key="group_year_level"
)
        exam_filter = st.multiselect("Exam Type", sorted(df["Exam"].unique()), default=[e for e in df["Exam"].unique() if "Continuous" not in e])

        filtered_df = df[(df["Student Name"] == student) & 
                         (df["Year Level"].isin(year_level_filter)) & 
                         (df["Exam"].isin(exam_filter))]

        if not filtered_df.empty:
            st.subheader("📚 Exam Results (Excluding Continuous Assessment)")
            fig, ax = plt.subplots(figsize=(12, 5))
            sns.barplot(data=filtered_df, x="Course", y="Score", hue="Year Level", ax=ax)
            ax.set_title(f"Scores by Course for {student}")
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
            st.pyplot(fig)
        else:
            st.info("No exam data to display.")

        ca_df = df[(df["Student Name"] == student) & (df["Exam"] == "Continuous Assessment")]
        if not ca_df.empty:
            st.subheader("📈 Continuous Assessment Trend")
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            sns.lineplot(data=ca_df, x="Academic Year", y="Score", marker="o", ax=ax2)
            ax2.set_title("Continuous Assessment Scores Over Years")
            st.pyplot(fig2)

    with tab2:
        st.header("Group Performance Analysis")
        program = st.selectbox("Program", sorted(df["Program"].dropna().unique()))
        class_group = st.selectbox("Class", sorted(df["Class"].dropna().unique()))
        year_level_group = st.multiselect("Year Level", sorted(df["Year Level"].dropna().unique()), default=sorted(df["Year Level"].dropna().unique()))
        exam_group_filter = st.multiselect("Exam Type", sorted(df["Exam"].unique()), default=[e for e in df["Exam"].unique() if "Continuous" not in e])

        group_df = df[(df["Program"] == program) & 
                      (df["Class"] == class_group) & 
                      (df["Year Level"].isin(year_level_group)) & 
                      (df["Exam"].isin(exam_group_filter))]

        if not group_df.empty:
            st.subheader("📊 Group Exam Performance")
            fig3, ax3 = plt.subplots(figsize=(12, 5))
            sns.barplot(data=group_df, x="Course", y="Score", hue="Exam", ax=ax3)
            ax3.set_title(f"Group Scores by Course - {class_group}")
            ax3.set_xticklabels(ax3.get_xticklabels(), rotation=45, ha="right")
            st.pyplot(fig3)
        else:
            st.info("No group exam data to display.")

        ca_group_df = df[(df["Program"] == program) & 
                         (df["Class"] == class_group) & 
                         (df["Exam"] == "Continuous Assessment")]

        if not ca_group_df.empty:
            st.subheader("📈 Continuous Assessment Trends (Group)")
            avg_df = ca_group_df.groupby(["Academic Year", "Course"]).mean(numeric_only=True).reset_index()
            fig4, ax4 = plt.subplots(figsize=(10, 4))
            sns.lineplot(data=avg_df, x="Academic Year", y="Score", hue="Course", marker="o", ax=ax4)
            ax4.set_title(f"Continuous Assessment Trends - {class_group}")
            st.pyplot(fig4)

            st.subheader("📊 Heatmap of CA Scores")
            pivot_data = avg_df.pivot(index="Course", columns="Academic Year", values="Score").fillna(0)
            fig5, ax5 = plt.subplots(figsize=(10, len(pivot_data) * 0.5))
            sns.heatmap(pivot_data, annot=True, cmap="YlGnBu", fmt=".0f", linewidths=0.5, ax=ax5)
            st.pyplot(fig5)
        else:
            st.info("No continuous assessment data for group.")

elif auth_status is False:
    st.error("Incorrect username or password.")
elif auth_status is None:
    st.warning("Please enter your credentials.")
