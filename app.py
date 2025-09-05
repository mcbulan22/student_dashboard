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

tab1, tab2, tab3 = st.tabs(["👤 Individual View", "👥 Group View", "🛠️ Interventions"])

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

# ===============================
# TAB 3: INTERVENTIONS / REMEDIATION (PROTECTED)
# ===============================
import datetime

with tab3:
    st.title("🛠️ Interventions — Protected Area")

    # --- Credentials (fallback + optional Sheet2)
    VALID_TAB3_USERS = {
        "admin": "password",
        "marlon": "password"
    }

    creds = VALID_TAB3_USERS.copy()
    try:
        if "df_users" in globals() and isinstance(df_users, pd.DataFrame):
            if "username" in df_users.columns and "password" in df_users.columns:
                for _, r in df_users.iterrows():
                    if pd.notna(r["username"]):
                        creds[str(r["username"]).strip()] = str(r["password"]) if pd.notna(r["password"]) else ""
    except Exception:
        pass

    if "tab3_authenticated" not in st.session_state:
        st.session_state["tab3_authenticated"] = False
    if "tab3_user" not in st.session_state:
        st.session_state["tab3_user"] = None

    if not st.session_state["tab3_authenticated"]:
        st.warning("This area is restricted. Please login to access interventions.")
        username_input = st.text_input("Username", key="tab3_user_input")
        password_input = st.text_input("Password", type="password", key="tab3_pass_input")

        if st.button("Login", key="tab3_loginbtn"):
            user_key = str(username_input).strip()
            pw = str(password_input)
            if user_key in creds and creds[user_key] == pw:
                st.session_state["tab3_authenticated"] = True
                st.session_state["tab3_user"] = user_key
                st.success("✅ Login successful. You may now access interventions.")
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Try again.")
    else:
        st.info(f"🔐 Logged in as **{st.session_state['tab3_user']}**")
        if st.button("Logout", key="tab3_logout"):
            st.session_state["tab3_authenticated"] = False
            st.session_state["tab3_user"] = None
            st.rerun()

        # -------------------------------
        # Tab 3 interventions logic
        # -------------------------------
        st.title("🛠️ Interventions — Identify & Plan")

        st.markdown("Use this tab to find **at-risk or performing** students/sections, "
                    "pick suggested interventions, and track progress.")

        # --- Filters
        st.subheader("1) Filters for analysis")
        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            exam_type_filter = st.selectbox("Exam Type (analysis)", ["All"] + sorted(df["Exam Type"].dropna().unique().tolist()))
            AY_filter = st.selectbox("AY (analysis)", ["All"] + sorted(df["AY"].dropna().unique().tolist()))
        with colf2:
            program_filter = st.selectbox("Program (analysis)", ["All"] + sorted(df["Program"].dropna().unique().tolist()))
            principal_filter_int = st.selectbox("Principal (analysis)", ["All"] + sorted(df["Principal"].dropna().unique().tolist()))
        with colf3:
            class_filter = st.selectbox("Class (analysis)", ["All"] + sorted(df["Class"].dropna().unique().tolist()))
            section_filter = st.selectbox("Section (analysis)", ["All"] + sorted(df["Section"].dropna().unique().tolist()))

        # --- Mode: At-risk or Performing
        st.subheader("2) Select analysis mode")
        analysis_mode = st.radio(
            "Which group do you want to analyze?",
            ["At-risk students/sections", "Performing students/sections"],
            horizontal=True
        )

        # --- Thresholds / rules
        st.subheader("3) Flagging rules")
        colt1, colt2, colt3 = st.columns(3)
        with colt1:
            absolute_thresh = st.slider("Absolute threshold", 40, 95, 60)
            high_absolute_thresh = st.slider("High performance threshold", 70, 100, 85)
        with colt2:
            relative_delta = st.slider("Relative delta (points vs section/program)", 0, 30, 10)
        with colt3:
            trend_detect = st.checkbox("Detect trend", value=True)
            neg_trend_thresh = st.number_input("Negative slope threshold", value=-0.5, format="%.2f")
            pos_trend_thresh = st.number_input("Positive slope threshold", value=0.5, format="%.2f")

        # --- Helper: apply filters
        def apply_analysis_filters(df_in):
            g = df_in.copy()
            if exam_type_filter != "All":
                g = g[g["Exam Type"] == exam_type_filter]
            if AY_filter != "All":
                g = g[g["AY"] == AY_filter]
            if program_filter != "All":
                g = g[g["Program"] == program_filter]
            if principal_filter_int != "All":
                g = g[g["Principal"] == principal_filter_int]
            if class_filter != "All":
                g = g[g["Class"] == class_filter]
            if section_filter != "All":
                g = g[g["Section"] == section_filter]
            return g

        df_analysis = apply_analysis_filters(df)
        st.markdown(f"Records considered: **{len(df_analysis)}**")

        if len(df_analysis) == 0:
            st.warning("⚠️ No records found for the selected filters. Please adjust filters.")
            st.stop()

        # --- Compute metrics (student + section)
        def ay_to_year(ay_str):
            try:
                return int(str(ay_str).split("-")[0])
            except:
                try:
                    return int(str(ay_str)[:4])
                except:
                    return None

        student_avg = (
            df_analysis.groupby(["Midshipman Number", "Full Name", "Section", "Class", "Program"])["Percentage Score"]
            .mean()
            .reset_index()
            .rename(columns={"Percentage Score": "Student_Avg"})
        )

        section_avg = (
            df_analysis.groupby(["Section"])["Percentage Score"]
            .mean()
            .reset_index()
            .rename(columns={"Percentage Score": "Section_Avg"})
        )

        student_flags = student_avg.merge(section_avg, on="Section", how="left")
        student_flags["Delta_vs_Section"] = student_flags["Student_Avg"] - student_flags["Section_Avg"]

        # Trend slopes
        slopes = []
        for midn, group in df_analysis.groupby("Midshipman Number"):
            g = group.groupby("AY")["Percentage Score"].mean().reset_index()
            g["AY_num"] = g["AY"].apply(ay_to_year)
            g = g.dropna(subset=["AY_num", "Percentage Score"])
            if len(g) < 2:
                slopes.append({"Midshipman Number": midn, "slope": 0.0, "points": len(g)})
                continue
            try:
                coeffs = np.polyfit(g["AY_num"], g["Percentage Score"], 1)
                slope = float(coeffs[0])
            except:
                slope = 0.0
            slopes.append({"Midshipman Number": midn, "slope": slope, "points": len(g)})
        slopes_df = pd.DataFrame(slopes)
        student_flags = student_flags.merge(slopes_df, on="Midshipman Number", how="left")

        # --- Decide flags (different for at-risk vs performing)
        def flag_reasons(row):
            reasons = []
            if analysis_mode == "At-risk students/sections":
                if row["Student_Avg"] < absolute_thresh:
                    reasons.append(f"Absolute<{absolute_thresh}")
                if row["Delta_vs_Section"] < -relative_delta:
                    reasons.append(f"{abs(row['Delta_vs_Section']):.1f}pt below section")
                if trend_detect and row.get("slope", 0) <= neg_trend_thresh and row.get("points", 0) >= 2:
                    reasons.append(f"Declining trend (slope={row['slope']:.2f})")
            else:  # Performing
                if row["Student_Avg"] > high_absolute_thresh:
                    reasons.append(f"Absolute>{high_absolute_thresh}")
                if row["Delta_vs_Section"] > relative_delta:
                    reasons.append(f"+{row['Delta_vs_Section']:.1f}pt above section")
                if trend_detect and row.get("slope", 0) >= pos_trend_thresh and row.get("points", 0) >= 2:
                    reasons.append(f"Improving trend (slope={row['slope']:.2f})")
            return "; ".join(reasons)

        student_flags["Reasons"] = student_flags.apply(flag_reasons, axis=1)

        # Filter students
        flagged_students = student_flags[student_flags["Reasons"] != ""].copy()

        if flagged_students.empty:
            st.info(f"No {analysis_mode.lower()} found with current rules/filters.")
            st.stop()

        # --- Section-level metrics
        sec_metrics = (
            df_analysis.groupby(["Section", "Program", "Class", "Principal"])["Percentage Score"]
            .agg(["mean", "count"])
            .reset_index()
            .rename(columns={"mean": "Section_Avg", "count": "N"})
        )

        program_avg = df_analysis.groupby("Program")["Percentage Score"].mean().reset_index().rename(columns={"Percentage Score": "Program_Avg"})
        sec_metrics = sec_metrics.merge(program_avg, on="Program", how="left")
        sec_metrics["Delta_vs_Program"] = sec_metrics["Section_Avg"] - sec_metrics["Program_Avg"]

        if analysis_mode == "At-risk students/sections":
            sec_metrics["Section_Reasons"] = sec_metrics.apply(
                lambda r: "; ".join(
                    [txt for txt in (
                        (f"SectionAvg<{absolute_thresh}" if r["Section_Avg"] < absolute_thresh else None),
                        (f"{abs(r['Delta_vs_Program']):.1f}pt below program" if r["Delta_vs_Program"] < -relative_delta else None),
                    ) if txt]
                ), axis=1
            )
        else:
            sec_metrics["Section_Reasons"] = sec_metrics.apply(
                lambda r: "; ".join(
                    [txt for txt in (
                        (f"SectionAvg>{high_absolute_thresh}" if r["Section_Avg"] > high_absolute_thresh else None),
                        (f"+{r['Delta_vs_Program']:.1f}pt above program" if r["Delta_vs_Program"] > relative_delta else None),
                    ) if txt]
                ), axis=1
            )

        flagged_sections = sec_metrics[sec_metrics["Section_Reasons"] != ""]


        # ---- UI: show flagged students
        st.subheader("3) Flagged students")
        st.markdown("Students flagged by the chosen rules. Review reasons, see weak courses, and assign interventions.")
        st.write(f"Total flagged students: **{len(flagged_students)}**")

        if len(flagged_students) > 0:
            # Compute weak courses per flagged student
            weak_courses_dict = {}
            for midn in flagged_students["Midshipman Number"]:
                stud_records = df_analysis[df_analysis["Midshipman Number"] == midn]
                # student average per course
                stud_course_avg = stud_records.groupby("Course")["Percentage Score"].mean().reset_index()
                # section average per course
                sec = flagged_students.loc[flagged_students["Midshipman Number"] == midn, "Section"].values[0]
                sec_records = df_analysis[df_analysis["Section"] == sec]
                sec_course_avg = sec_records.groupby("Course")["Percentage Score"].mean().reset_index()
                merged = pd.merge(stud_course_avg, sec_course_avg, on="Course", how="inner", suffixes=("_student", "_section"))
                # flag weak courses
                merged["Gap"] = merged["Percentage Score_student"] - merged["Percentage Score_section"]
                weak_list = merged[merged["Gap"] < -relative_delta]["Course"].tolist()
                weak_courses_dict[midn] = weak_list if weak_list else []

            flagged_students["Weak Courses"] = flagged_students["Midshipman Number"].map(weak_courses_dict)

            st.dataframe(flagged_students[[
                "Full Name", "Midshipman Number", "Section", "Class", "Program",
                "Student_Avg", "Section_Avg", "Delta_vs_Section", "slope", "points", "Reasons", "Weak Courses"
            ]].sort_values("Student_Avg"))

            # quick bar chart of lowest performing students
            st.subheader("Lowest performing flagged students")
            low_df = flagged_students.sort_values("Student_Avg").head(10)
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.barh(low_df["Full Name"] + " (" + low_df["Midshipman Number"] + ")", low_df["Student_Avg"])
            ax.set_xlim(0, 100)
            ax.set_xlabel("Average % Score")
            ax.set_title("Lowest flagged students")
            st.pyplot(fig)


        # ---- UI: flagged sections
        st.subheader("4) Flagged sections")
        st.write(f"Total flagged sections: **{len(flagged_sections)}**")
        if len(flagged_sections) > 0:
            st.dataframe(flagged_sections[["Section", "Program", "Class", "N", "Section_Avg", "Program_Avg", "Delta_vs_Program", "Section_Reasons"]])
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            tmp = flagged_sections.sort_values("Section_Avg").head(10)
            ax2.barh(tmp["Section"] + " - " + tmp["Program"], tmp["Section_Avg"])
            ax2.set_xlim(0, 100)
            ax2.set_xlabel("Section Avg % Score")
            ax2.set_title("Lowest flagged sections")
            st.pyplot(fig2)
        else:
            st.info("No sections flagged with current filters/rules.")

        # ---- Intervention suggestions (automated heuristics)
        st.subheader("5) Suggested interventions (automated)")
        def suggest_interventions(reason_text, student_avg, delta, slope):
            # produce prioritized suggestions (list)
            recs = []
            # if broad low performance
            if "Absolute" in reason_text and student_avg < absolute_thresh:
                recs += [
                    "Assign remedial modular kit (self-paced modules)",
                    "Schedule weekly skills lab / supervised practice",
                    "Assign peer tutor (same section)",
                    "Assign formative quizzes and mastery checks"
                ]
            # if below section by a lot
            if "below section" in reason_text:
                recs += [
                    "One-on-one tutoring on weak courses",
                    "Diagnostic assessment to identify gaps",
                    "Instructor review of lesson pacing for those courses"
                ]
            # trend
            if "Declining" in reason_text or slope < trend_slope_thresh:
                recs += [
                    "Mentor check-in and study plan",
                    "Counseling / academic advising",
                    "Short-term progress checkpoint (2 weeks)"
                ]
            # exam type specific hints
            if str(exam_type_filter).lower().find("final") >= 0:
                recs += ["Exam skills workshop: time management, question analysis, mock exam under exam conditions"]
            if str(exam_type_filter).lower().find("outcome") >= 0 or str(exam_type_filter).lower().find("coa") >= 0:
                recs += ["Competency-focused remediation: supervised practice in skills/simulator"]
            # unique & dedupe
            unique = []
            for r in recs:
                if r not in unique:
                    unique.append(r)
            return unique

        # show suggestions for each flagged student (collapsible)
        if len(flagged_students) > 0:
            for _, r in flagged_students.head(50).iterrows():
                with st.expander(f"{r['Full Name']} ({r['Midshipman Number']}) — Reasons: {r['Reasons']}"):
                    st.write({
                        "Student Avg": round(r["Student_Avg"], 2),
                        "Section Avg": round(r["Section_Avg"], 2) if pd.notna(r["Section_Avg"]) else None,
                        "Delta": round(r["Delta_vs_Section"], 2),
                        "Trend slope": round(r.get("slope", 0), 3),
                    })
                    recs = suggest_interventions(r["Reasons"], r["Student_Avg"], r["Delta_vs_Section"], r.get("slope", 0))
                    st.markdown("**Recommended interventions:**")
                    for rec in recs:
                        st.write("- " + rec)

                    # allow planner to create an intervention entry
                    st.markdown("**Create intervention**")
                    default_start = datetime.date.today()
                    start_dt = st.date_input("Start date", value=default_start, key=f"start_{r['Midshipman Number']}")
                    due_dt = st.date_input("Due date", value=default_start + datetime.timedelta(days=14), key=f"due_{r['Midshipman Number']}")
                    assigned_to = st.text_input("Assigned to (tutor/mentor)", key=f"assign_{r['Midshipman Number']}")
                    intervention_choice = st.selectbox("Pick recommended action", ["Custom"] + recs, key=f"pickrec_{r['Midshipman Number']}")
                    custom_note = st.text_area("Notes / steps", key=f"note_{r['Midshipman Number']}")
                    if st.button("Save intervention", key=f"save_{r['Midshipman Number']}"):
                        # store in session_state interventions list
                        if "interventions" not in st.session_state:
                            st.session_state["interventions"] = []
                        action = intervention_choice if intervention_choice != "Custom" else custom_note
                        st.session_state["interventions"].append({
                            "Full Name": r["Full Name"],
                            "Midshipman Number": r["Midshipman Number"],
                            "Section": r["Section"],
                            "Reason": r["Reasons"],
                            "Action": action,
                            "Assigned To": assigned_to,
                            "Start": str(start_dt),
                            "Due": str(due_dt),
                            "Status": "Planned",
                            "Notes": custom_note
                        })
                        st.success("Intervention saved (session).")

        # ---- Show / manage interventions saved in session
        st.subheader("6) Saved interventions (local session)")
        if "interventions" not in st.session_state:
            st.write("No interventions saved yet in this session.")
        else:
            interventions_df = pd.DataFrame(st.session_state["interventions"])
            st.dataframe(interventions_df)

            # allow status update
            idx = st.number_input("Select row index to change status (0-based)", min_value=0, max_value=len(interventions_df)-1, value=0)
            new_status = st.selectbox("New status", ["Planned", "In progress", "Completed"], key="new_status_key")
            if st.button("Update status"):
                st.session_state["interventions"][idx]["Status"] = new_status
                st.success("Status updated.")
                st.rerun()

            # allow export
            csv = interventions_df.to_csv(index=False)
            st.download_button("Download interventions CSV", data=csv, file_name="interventions.csv", mime="text/csv")
