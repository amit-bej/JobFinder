
import streamlit as st
from utils.Rag import *
from utils.text_extractor import extract_text_from_file
from scrapper.scrapper import scrape_naukri
import pandas as pd
import json
import re
import os
import io

st.set_page_config(page_title="Job Finder Assistant", layout="wide")

st.title("Job Finder Assistant")

@st.cache_resource
def get_chroma_collection():
    return initializeChroma()

collection = get_chroma_collection()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()
with st.sidebar:
    st.header("Upload Resume")
    uploaded_files = st.file_uploader(
        "Upload documents (PDF, DOCX, TXT)", 
        type=['txt', 'pdf', 'docx'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        with st.spinner("Processing resume..."):
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in st.session_state.processed_files:
                    text = extract_text_from_file(uploaded_file)
                    
                    if text.startswith("Error"):
                        st.error(f"Failed to process {uploaded_file.name}: {text}")
                    else:
                        process_and_store_document(collection, text)
                        st.session_state.processed_files.add(uploaded_file.name)
                        if "resume_data" in st.session_state:
                            del st.session_state.resume_data
                        st.toast(f"Indexed {uploaded_file.name}")
            
    st.markdown("---")
    st.markdown(f"**Indexed Files:** {len(st.session_state.processed_files)}")
    for file in st.session_state.processed_files:
        st.caption(f"- {file}")


if st.session_state.processed_files:
    if "resume_data" not in st.session_state:
        with st.spinner("Analyzing resume with AI..."):
            response_data = generateResponse(
                collection,
                "Extract only the skills and the total years of work experience from the resume. \
            Return strictly in JSON with the following keys: \
            'skills' as a list of skill names, and 'total_years_experience' as a number only. \
            Do not include experience descriptions or job history."
            )
            st.session_state.resume_data = response_data

    response_data = st.session_state.resume_data

    response_text = response_data["message"]["content"]
    #print(response_text)
    response_text = re.sub(r'```json\s*|\s*```', '', response_text)
    
    try:
        resume_data = json.loads(response_text)
        st.success("Resume processed successfully!")
        
        resume_skills = [s.lower().strip() for s in resume_data.get("skills", [])]
        
        raw_exp = resume_data.get("total_years_experience", 0)
        try:
            resume_experience = int(float(str(raw_exp)))
        except:
            nums = re.findall(r'\d+', str(raw_exp))
            resume_experience = int(nums[0]) if nums else 0
        
        st.write(f"**Detected Skills:** {', '.join(resume_data.get('skills', []))}")
        st.write(f"**Detected Experience:** {resume_experience} years")
        
        st.markdown("### Scrape Settings")
        col1, col2, col3= st.columns(3)
        with col1:
            role_input = st.text_input("Job Role", value="Python Developer")
        with col2:
            location_input = st.text_input("Location", value="Hyderabad")
        with col3:
            pagestart_input = st.number_input("Page number to start from (scrapes +10 pages at a time)", value=1)

        if "show_results" not in st.session_state:
            st.session_state.show_results = False

        if st.button("Scrape Jobs"):
            with st.spinner(f"Scraping {role_input} jobs in {location_input} for {resume_experience} years experience..."):
                try:
                    df_result = scrape_naukri(
                        role=role_input,
                        location=location_input,
                        experience=resume_experience,
                        page_start=pagestart_input
                    )
                    
                    st.session_state.show_results = True
                    st.success(f"Scraping completed! Found {len(df_result)} jobs. Reloading...")
                    st.cache_data.clear()
                    
                except Exception as e:
                    st.error(f"Error running scraper: {e}")
        
        jobs_df = pd.DataFrame()
        if st.session_state.show_results:
            try:
                if os.path.exists("naukri_jobs.csv") and os.path.getsize("naukri_jobs.csv") > 0:
                    jobs_df = pd.read_csv("naukri_jobs.csv")
                else:
                    pass
            except pd.errors.EmptyDataError:
                st.error("Job database file is empty. Please scrape jobs again.")
            except FileNotFoundError:
                st.error("Job database (naukri_jobs.csv) not found. Please run the scraper first.") 

            if not jobs_df.empty:
                st.info(f"DEBUGGING: Loaded {len(jobs_df)} jobs. Resume Experience: {resume_experience} years.")
                st.write(f"DEBUG: Resume Skills: {resume_skills}")

                def calculate_match(row):
                    job_skills_str = row["Skill"]
                    if not isinstance(job_skills_str, str):
                        skill_score = 0
                        matched_skills = []
                    else:
                        job_skills = [s.lower().strip() for s in job_skills_str.split(',')]
                        matched_skills = [s for s in job_skills if any(rs in s or s in rs for rs in resume_skills)]
                        skill_score = len(matched_skills)
                    
                    exp_str = str(row.get("Experience", ""))
                    exp_match = False
                    try:
                        years = re.findall(r'\d+', exp_str)
                        if years:
                            min_exp = int(years[0])
                            max_exp = int(years[1]) if len(years) > 1 else min_exp + 5
                            
                            if min_exp <= resume_experience <= max_exp:
                                exp_match = True
                            elif resume_experience >= min_exp:
                                exp_match = True
                    except:
                        pass
                    
                    return skill_score, matched_skills, exp_match

                results = jobs_df.apply(calculate_match, axis=1)
                jobs_df["Match Score"] = [res[0] for res in results]
                jobs_df["Matched Skills"] = [res[1] for res in results]
                jobs_df["Exp Match"] = [res[2] for res in results]
                
                filtered_jobs = jobs_df[
                    (jobs_df["Match Score"] > 0) & 
                    (jobs_df["Exp Match"] == True)
                ].sort_values(by="Match Score", ascending=False)
                
                st.header(f"Recommended Jobs ({len(filtered_jobs)})")
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    filtered_jobs.to_excel(writer, index=False)
                
                st.download_button(
                    label="Download Results as Excel",
                    data=buffer.getvalue(),
                    file_name="recommended_jobs.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                for _, row in filtered_jobs.iterrows():
                    with st.expander(f"{row['Title']} at {row['Company Name']} (Match: {row['Match Score']}, Exp: {row['Experience']})"):
                        st.write(f"**Skills:** {row['Skill']}")
                        st.write(f"**Matched:** {', '.join(row['Matched Skills'])}")
                        st.write(f"**Experience:** {row['Experience']}")
                        if pd.notna(row['Link']) and row['Link'] != "NA":
                            st.markdown(f"[Apply Now]({row['Link']})")
                        else:
                            st.write("Link not available")
            else:
                 st.warning("No jobs found. Use the 'Scrape Jobs' button to fetch new data.")

    except json.JSONDecodeError:
        st.error(f"Failed to parse AI response: {response_text}")
else:
    st.info("Please upload a resume to see job recommendations.")


