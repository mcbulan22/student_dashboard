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
        student_df = df[df["Midshipman Number"] == midn].copy()
    
        if student_df.empty:
            st.warning("No records found for this student.")
        else:
            # Basic student info
            student_name = student_df["Full Name"].iloc[0]
            section = student_df["Section"].iloc[0] if "Section" in student_df.columns else ""
            AY_student = student_df["AY"].iloc[0] if "AY" in student_df.columns else None
            program_student = student_df["Program"].iloc[0] if "Program" in student_df.columns else None
            class_student = student_df["Class"].iloc[0] if "Class" in student_df.columns else None
    
            st.subheader(f"📈 Academic Profile: {student_name}")
            st.dataframe(student_df)
    
            # Helper: prepare mean scores per normalized course
            def prepare_scores(df_in):
                d = df_in.copy()
                if "Course" not in d.columns or "Percentage Score" not in d.columns:
                    return pd.DataFrame(columns=["Course_key", "Percentage Score"])
                d["Course_key"] = d["Course"].astype(str).str.strip().str.upper()
                d["Percentage Score"] = pd.to_numeric(d["Percentage Score"], errors="coerce")
                d = d.dropna(subset=["Course_key", "Percentage Score"])
                out = d.groupby("Course_key", as_index=False)["Percentage Score"].mean()
                return out
    
            def plot_merged_radar(merged_df, title, level_label):
                """
                merged_df expected columns:
                  - Course_key
                  - Percentage Score_student
                  - Percentage Score_comp
                """
                if merged_df.empty:
                    st.warning(f"No overlapping courses to plot for {title} when comparing to {level_label}.")
                    return
            
                # Ensure stable ordering
                merged_df = merged_df.sort_values("Course_key").reset_index(drop=True)
            
                courses = merged_df["Course_key"].tolist()
                vals_student = merged_df["Percentage Score_student"].tolist()
                vals_comp = merged_df["Percentage Score_comp"].tolist()
                N = len(courses)
            
                # Fallback for too few categories: use bar chart
                if N < 3:
                    fig, ax = plt.subplots(figsize=(6, 4))
                    x = np.arange(N)
                    width = 0.35
                    ax.bar(x - width/2, vals_student, width, label="Student")
                    ax.bar(x + width/2, vals_comp, width, label=f"{level_label} Avg")
                    ax.set_xticks(x)
                    ax.set_xticklabels(courses, rotation=30, ha="right")
                    ax.set_ylim(0, 100)
                    ax.set_ylabel("Percentage Score")
                    ax.set_title(f"{title} — {level_label} (Bar fallback for <3 courses)")
                    ax.legend()
                    st.pyplot(fig)
                    return
            
                # Radar plotting for N >= 3
                # angles for N categories, then extend by repeating first angle to close loop
                angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
                angles += angles[:1]  # now length N+1
            
                vals_student_loop = vals_student + vals_student[:1]
                vals_comp_loop = vals_comp + vals_comp[:1]
            
                fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                ax.plot(angles, vals_student_loop, label="Student", linewidth=2)
                ax.fill(angles, vals_student_loop, alpha=0.25)
                ax.plot(angles, vals_comp_loop, linestyle="dashed", label=f"{level_label} Avg", linewidth=2)
                ax.fill(angles, vals_comp_loop, alpha=0.15)
            
                # Use angles[:-1] and original courses for labels (prevents duplicated label showing)
                ax.set_thetagrids(np.degrees(angles[:-1]), courses)
                ax.set_ylim(0, 100)
                ax.set_title(f"{title} — Compared to {level_label}", size=14, weight="bold", pad=12)
                ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))
            
                st.pyplot(fig)
    
            # Helper: student-only radar (no comparison)
            def plot_student_only(student_scores_df, title):
                """
                student_scores_df expected columns:
                  - Course_key
                  - Percentage Score
                """
                if student_scores_df.empty:
                    st.warning(f"No student data to plot for {title}.")
                    return
            
                student_scores_df = student_scores_df.sort_values("Course_key").reset_index(drop=True)
                courses = student_scores_df["Course_key"].tolist()
                vals_student = student_scores_df["Percentage Score"].tolist()
                N = len(courses)
            
                # Fallback to bar if fewer than 3 courses
                if N < 3:
                    fig, ax = plt.subplots(figsize=(6, 4))
                    x = np.arange(N)
                    ax.bar(x, vals_student, width=0.6, label="Student")
                    ax.set_xticks(x)
                    ax.set_xticklabels(courses, rotation=30, ha="right")
                    ax.set_ylim(0, 100)
                    ax.set_ylabel("Percentage Score")
                    ax.set_title(title + " — Student only (Bar fallback for <3 courses)")
                    ax.legend()
                    st.pyplot(fig)
                    return
            
                # Radar for N >= 3
                angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
                angles += angles[:1]  # close loop
            
                vals_student_loop = vals_student + vals_student[:1]
            
                fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                ax.plot(angles, vals_student_loop, label="Student", linewidth=2)
                ax.fill(angles, vals_student_loop, alpha=0.25)
            
                ax.set_thetagrids(np.degrees(angles[:-1]), courses)
                ax.set_ylim(0, 100)
                ax.set_title(title + " — Student only", size=14, weight="bold", pad=12)
                ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))
            
                st.pyplot(fig)
    
            # Core logic to get student & comparison frames for an exam type (with fallbacks)
            def get_student_and_comparison(exam_type_label):
                # Accept flexible exam type matching (case-insensitive, substring)
                mask_student = student_df["Exam Type"].astype(str).str.contains(exam_type_label, case=False, na=False)
                student_scores = prepare_scores(student_df[mask_student])
    
                # candidate comparison levels (ordered)
                comparison_levels = []
    
                # Section level
                if section:
                    df_section = df[df["Section"] == section]
                    df_section_mask = df_section[df_section["Exam Type"].astype(str).str.contains(exam_type_label, case=False, na=False)]
                    comparison_levels.append(("Section", df_section_mask))
    
                # Class level
                if class_student:
                    df_class = df[(df["Class"] == class_student) & (df["AY"] == AY_student)]
                    df_class_mask = df_class[df_class["Exam Type"].astype(str).str.contains(exam_type_label, case=False, na=False)]
                    comparison_levels.append(("Class", df_class_mask))
    
                # Program + AY level
                if program_student and AY_student:
                    df_prog = df[(df["Program"] == program_student) & (df["AY"] == AY_student)]
                    df_prog_mask = df_prog[df_prog["Exam Type"].astype(str).str.contains(exam_type_label, case=False, na=False)]
                    comparison_levels.append(("Program+AY", df_prog_mask))
    
                # AY + Program fallback already covered; last resort: all students for the exam type
                df_all_mask = df[df["Exam Type"].astype(str).str.contains(exam_type_label, case=False, na=False)]
                comparison_levels.append(("All Students", df_all_mask))
    
                # Evaluate each level to find best comparison that has overlap with student's courses
                for level_name, lvl_df in comparison_levels:
                    comp_scores = prepare_scores(lvl_df)
                    # check if there is at least one common course_key
                    if not student_scores.empty and not comp_scores.empty:
                        common = set(student_scores["Course_key"]).intersection(set(comp_scores["Course_key"]))
                        if len(common) > 0:
                            # reduce to only overlapping courses, then prepare merged frame
                            stud_sub = student_scores[student_scores["Course_key"].isin(common)].copy()
                            comp_sub = comp_scores[comp_scores["Course_key"].isin(common)].copy()
                            merged = pd.merge(stud_sub, comp_sub, on="Course_key", how="inner", suffixes=("_student", "_comp"))
                            return student_scores, comp_scores, merged, level_name
    
                # No overlapping comparison found; return what we have (student_scores may be empty) and None for merged/level
                return student_scores, pd.DataFrame(columns=["Course_key", "Percentage Score"]), pd.DataFrame(), None
    
            # --- Final Term Exam Radar ---
            fte_student_scores, fte_comp_scores, fte_merged, fte_level = get_student_and_comparison("final")
            if not fte_merged.empty:
                st.info(f"Final Term Exam — comparison level used: {fte_level}")
                st.write("Merged (Final Term Exam) sample:", fte_merged.head())
                plot_merged_radar(fte_merged, "Final Term Exam Performance", fte_level)
            else:
                # if no merged overlap but student has FTE data, show student-only radar with an info message
                if not fte_student_scores.empty:
                    st.info("No matching comparison group found for Final Term Exam — showing student-only radar.")
                    st.write("Student (Final Term Exam) sample:", fte_student_scores.head())
                    plot_student_only(fte_student_scores, "Final Term Exam Performance")
                else:
                    st.warning("No Final Term Exam records found for this student.")
    
            # --- Course Outcome Assessment Radar ---
            coa_student_scores, coa_comp_scores, coa_merged, coa_level = get_student_and_comparison("course outcome|coa")
            if not coa_merged.empty:
                st.info(f"Course Outcome Assessment — comparison level used: {coa_level}")
                st.write("Merged (COA) sample:", coa_merged.head())
                plot_merged_radar(coa_merged, "Course Outcome Assessment Performance", coa_level)
            else:
                if not coa_student_scores.empty:
                    st.info("No matching comparison group found for COA — showing student-only radar.")
                    st.write("Student (COA) sample:", coa_student_scores.head())
                    plot_student_only(coa_student_scores, "Course Outcome Assessment Performance")
                else:
                    st.warning("No Course Outcome Assessment records found for this student.")



# ===============================
# TAB 2: GROUP VIEW (with enable/disable filters)
# ===============================
with tab2:
    st.title("📊 Group Performance Comparison")

    col_left, col_right = st.columns(2)

    # --- Group A UI ---
    with col_left:
        st.subheader("🔹 Group A")
        enable_all_a = st.checkbox("Enable all filters (Group A)", value=False, key="enable_all_a")

        # AY
        enable_ay_a = st.checkbox("Enable AY filter (A)", value=enable_all_a, key="enable_ay_a")
        AY_A = st.selectbox("AY (Group A)", sorted(df["AY"].dropna().unique()), key="ay_a") if enable_ay_a else None

        # Program
        enable_prog_a = st.checkbox("Enable Program filter (A)", value=enable_all_a, key="enable_prog_a")
        prog_A = st.selectbox("Program (Group A)", sorted(df["Program"].dropna().unique()), key="prog_a") if enable_prog_a else None

        # Section
        enable_sec_a = st.checkbox("Enable Section filter (A)", value=enable_all_a, key="enable_sec_a")
        sec_A = st.selectbox("Section (Group A)", sorted(df["Section"].dropna().unique()), key="sec_a") if enable_sec_a else None

        # Class
        enable_cls_a = st.checkbox("Enable Class filter (A)", value=enable_all_a, key="enable_cls_a")
        cls_A = st.selectbox("Class (Group A)", sorted(df["Class"].dropna().unique()), key="cls_a") if enable_cls_a else None

        # Exam Type
        enable_exam_a = st.checkbox("Enable Exam Type filter (A)", value=enable_all_a, key="enable_exam_a")
        exam_A = st.selectbox("Exam Type (Group A)", sorted(df["Exam Type"].dropna().unique()), key="exam_a") if enable_exam_a else None

        # Principal
        enable_princ_a = st.checkbox("Enable Principal filter (A)", value=enable_all_a, key="enable_princ_a")
        principal_A = st.selectbox("Principal (Group A)", sorted(df["Principal"].dropna().unique()), key="princ_a") if enable_princ_a else None

    # --- Group B UI ---
    with col_right:
        st.subheader("🔸 Group B")
        enable_all_b = st.checkbox("Enable all filters (Group B)", value=False, key="enable_all_b")

        enable_ay_b = st.checkbox("Enable AY filter (B)", value=enable_all_b, key="enable_ay_b")
        AY_B = st.selectbox("AY (Group B)", sorted(df["AY"].dropna().unique()), key="ay_b") if enable_ay_b else None

        enable_prog_b = st.checkbox("Enable Program filter (B)", value=enable_all_b, key="enable_prog_b")
        prog_B = st.selectbox("Program (Group B)", sorted(df["Program"].dropna().unique()), key="prog_b") if enable_prog_b else None

        enable_sec_b = st.checkbox("Enable Section filter (B)", value=enable_all_b, key="enable_sec_b")
        sec_B = st.selectbox("Section (Group B)", sorted(df["Section"].dropna().unique()), key="sec_b") if enable_sec_b else None

        enable_cls_b = st.checkbox("Enable Class filter (B)", value=enable_all_b, key="enable_cls_b")
        cls_B = st.selectbox("Class (Group B)", sorted(df["Class"].dropna().unique()), key="cls_b") if enable_cls_b else None

        enable_exam_b = st.checkbox("Enable Exam Type filter (B)", value=enable_all_b, key="enable_exam_b")
        exam_B = st.selectbox("Exam Type (Group B)", sorted(df["Exam Type"].dropna().unique()), key="exam_b") if enable_exam_b else None

        enable_princ_b = st.checkbox("Enable Principal filter (B)", value=enable_all_b, key="enable_princ_b")
        principal_B = st.selectbox("Principal (Group B)", sorted(df["Principal"].dropna().unique()), key="princ_b") if enable_princ_b else None

    # --- Apply filters only if their enable-checkbox is True ---
    def apply_filters(source_df, AY, prog, sec, cls, exam, principal):
        g = source_df.copy()
        if AY is not None:
            g = g[g["AY"] == AY]
        if prog is not None:
            g = g[g["Program"] == prog]
        if sec is not None:
            g = g[g["Section"] == sec]
        if cls is not None:
            g = g[g["Class"] == cls]
        if exam is not None:
            g = g[g["Exam Type"] == exam]
        if principal is not None:
            g = g[g["Principal"] == principal]
        return g

    groupA = apply_filters(df, AY_A, prog_A, sec_A, cls_A, exam_A, principal_A)
    groupB = apply_filters(df, AY_B, prog_B, sec_B, cls_B, exam_B, principal_B)

    # Show summary of active filters for clarity
    with st.expander("Active filters (Group A)"):
        st.write({
            "AY": AY_A, "Program": prog_A, "Section": sec_A,
            "Class": cls_A, "Exam Type": exam_A, "Principal": principal_A
        })
        st.write(f"Records found: {len(groupA)}")
    with st.expander("Active filters (Group B)"):
        st.write({
            "AY": AY_B, "Program": prog_B, "Section": sec_B,
            "Class": cls_B, "Exam Type": exam_B, "Principal": principal_B
        })
        st.write(f"Records found: {len(groupB)}")

    # Compare (only aggregated, hide PII)
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
        st.warning("One or both groups have no data (check enabled filters).")
