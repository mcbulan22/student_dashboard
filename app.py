import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from PIL import Image

# Load logo
logo = Image.open("maap_logo.png")

# --- Load Data ---
df = pd.read_excel("students.xlsx", sheet_name="Sheet1")
df_users = pd.read_excel("students.xlsx", sheet_name="Sheet2")

# --- Session State ---
if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.user = None
    st.session_state.midn = None

# --- Layout Header ---
col1, col2 = st.columns([1, 5])
with col1:
    st.image(logo, width=100)
with col2:
    st.markdown("## CCA Student Assessment Performance Dashboard")

tab1, tab2 = st.tabs(["👤 Individual View", "👥 Group View"])

# ===============================
# TAB 1: INDIVIDUAL VIEW
# ===============================
with tab1:
    if not st.session_state.login:
        st.title("🔐 Individual Student View - Login Required")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.button("Login")

        if login_btn:
            match = df_users[(df_users["username"] == username) & (df_users["password"] == password)]
            if not match.empty:
                st.session_state.login = True
                st.session_state.user = username
        
                # Find student's MIDN from Sheet1 by matching email or username
                student_match = df[(df["Email address"] == username) | (df["Midshipman Number"] == username)]
                if not student_match.empty:
                    st.session_state.midn = student_match["Midshipman Number"].iloc[0]
                else:
                    st.session_state.midn = None
        
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    else:
        # Logged in
        midn = st.session_state.midn
        student_df = df[df["Midshipman Number"] == midn]
    
        if student_df.empty:
            st.warning("No records found for this student.")
        else:
            student_name = student_df["Full Name"].iloc[0]
            section = student_df["Section"].iloc[0]
            st.subheader(f"📈 Academic Profile: {student_name}")
            st.dataframe(student_df)
    
        def radar_chart(student_df, section_df, title):
            if student_df.empty or section_df.empty:
                st.warning(f"No data available for {title}")
                return
        
            # Normalize course names
            student_df["Course"] = student_df["Course"].str.strip().str.upper()
            section_df["Course"] = section_df["Course"].str.strip().str.upper()
        
            # Merge
            merged = pd.merge(
                student_df,
                section_df,
                on="Course",
                how="inner",
                suffixes=("_student", "_section")
            )
        
            if merged.empty:
                st.warning(f"No matching courses found for {title}")
                return
        
            categories = merged["Course"].tolist()
            values_student = merged["Percentage Score_student"].tolist()
            values_section = merged["Percentage Score_section"].tolist()
        
            # Close the loop by appending first element only ONCE
            categories += [categories[0]]
            values_student += [values_student[0]]
            values_section += [values_section[0]]
        
            # Angles: must match categories length
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        
            # Radar plot
            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
            ax.plot(angles, values_student, label="Student", linewidth=2)
            ax.fill(angles, values_student, alpha=0.25)
        
            ax.plot(angles, values_section, linestyle="dashed", label="Section Avg", linewidth=2)
            ax.fill(angles, values_section, alpha=0.25)
        
            ax.set_thetagrids(np.degrees(angles), categories)
            ax.set_title(title, size=14, weight="bold", pad=20)
            ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))
        
            st.pyplot(fig)

            # === Prepare datasets ===
            # Final Term Exam
            fte_student = (
                student_df[student_df["Exam Type"] == "Final Term Exam"]
                .groupby("Course", as_index=False)["Percentage Score"]
                .mean()
            )
            fte_section = (
                df[(df["Exam Type"] == "Final Term Exam") & (df["Section"] == section)]
                .groupby("Course", as_index=False)["Percentage Score"]
                .mean()
            )
            if not fte_student.empty and not fte_section.empty:
                radar_chart(fte_student, fte_section, "Final Term Exam Performance")
    
            # Course Outcome Assessment
            coa_student = (
                student_df[student_df["Exam Type"] == "Course Outcome Assessment"]
                .groupby("Course", as_index=False)["Percentage Score"]
                .mean()
            )
            coa_section = (
                df[(df["Exam Type"] == "Course Outcome Assessment") & (df["Section"] == section)]
                .groupby("Course", as_index=False)["Percentage Score"]
                .mean()
            )
            if not coa_student.empty and not coa_section.empty:
                radar_chart(coa_student, coa_section, "Course Outcome Assessment Performance")


# ===============================
# TAB 2: GROUP VIEW
# ===============================
with tab2:
    st.title("📊 Group Performance Comparison")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🔹 Group A")
        AY_A = st.selectbox("AY (Group A)", sorted(df["AY"].unique()), key="ay_a")
        prog_A = st.selectbox("Program (Group A)", sorted(df["Program"].unique()), key="prog_a")
        sec_A = st.selectbox("Section (Group A)", sorted(df["Section"].unique()), key="sec_a")
        cls_A = st.selectbox("Class (Group A)", sorted(df["Class"].unique()), key="cls_a")
        exam_A = st.selectbox("Exam Type (Group A)", sorted(df["Exam Type"].unique()), key="exam_a")
        principal_A = st.selectbox("Principal (Group A)", sorted(df["Principal"].unique()), key="princ_a")

    with col_right:
        st.subheader("🔸 Group B")
        AY_B = st.selectbox("AY (Group B)", sorted(df["AY"].unique()), key="ay_b")
        prog_B = st.selectbox("Program (Group B)", sorted(df["Program"].unique()), key="prog_b")
        sec_B = st.selectbox("Section (Group B)", sorted(df["Section"].unique()), key="sec_b")
        cls_B = st.selectbox("Class (Group B)", sorted(df["Class"].unique()), key="cls_b")
        exam_B = st.selectbox("Exam Type (Group B)", sorted(df["Exam Type"].unique()), key="exam_b")
        principal_B = st.selectbox("Principal (Group B)", sorted(df["Principal"].unique()), key="princ_b")

    # Filter data
    groupA = df[(df["AY"] == AY_A) & (df["Program"] == prog_A) & (df["Section"] == sec_A) &
                (df["Class"] == cls_A) & (df["Exam Type"] == exam_A) & (df["Principal"] == principal_A)]
    groupB = df[(df["AY"] == AY_B) & (df["Program"] == prog_B) & (df["Section"] == sec_B) &
                (df["Class"] == cls_B) & (df["Exam Type"] == exam_B) & (df["Principal"] == principal_B)]

    if not groupA.empty and not groupB.empty:
        avgA = groupA.groupby("Course")["Percentage Score"].mean().reset_index().rename(columns={"Percentage Score": "Group A"})
        avgB = groupB.groupby("Course")["Percentage Score"].mean().reset_index().rename(columns={"Percentage Score": "Group B"})
        comp_df = pd.merge(avgA, avgB, on="Course", how="outer").fillna(0)

        st.subheader("📊 Side-by-Side Comparison")
        fig, ax = plt.subplots(figsize=(10, 6))
        comp_df.plot(x="Course", y=["Group A", "Group B"], kind="bar", ax=ax)
        ax.set_ylabel("Average % Score")
        ax.set_title("Group Comparison")
        st.pyplot(fig)
    else:
        st.warning("One or both groups have no data.")
