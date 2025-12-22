
import streamlit as st
from utils.Rag import *
from utils.text_extractor import extract_text_from_file
from scrapper.scrapper import scrape_naukri
import pandas as pd
import json
import re
import os
import io
import utils.tavilyclient as tavilyclient
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
        type=["txt", "pdf", "docx"],
        accept_multiple_files=True
    )

    if st.button("Embed resume") and uploaded_files:
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

    # -------------------------------
    # Job domains selection section
    # -------------------------------
    st.markdown("---")
    st.header("Job Domains")

    default_domains = [
        "linkedin.com",
        "naukri.com",
        "indeed.com",
        "glassdoor.com",
        "foundit.in"
    ]

    if "custom_domains" not in st.session_state:
        st.session_state.custom_domains = []

    selected_domains = st.multiselect(
        "Select job portals",
        options=default_domains,
        default=default_domains
    )

    custom_domain = st.text_input(
        "Add custom domain (e.g. company.com or jobboard.com)"
    )

    if st.button("Add Domain"):
        if custom_domain:
            domain = custom_domain.strip().lower()
            if domain not in st.session_state.custom_domains and domain not in default_domains:
                st.session_state.custom_domains.append(domain)
                st.rerun()

    if st.session_state.custom_domains:
        st.caption(f"Custom: {', '.join(st.session_state.custom_domains)}")
        if st.button("Clear Custom Domains"):
            st.session_state.custom_domains = []
            st.rerun()

    active_domains = selected_domains + st.session_state.custom_domains
    st.session_state.domains = active_domains

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
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            role_input = st.text_input("Job Role", value="Python Developer")
        with col2:
            location_input = st.text_input("Location", value="Hyderabad")
        with col3:
            total_jobs_to_find = st.number_input("Total jobs", value=15)
        with col4:
            days_filter = st.number_input("Post Recency (Days)", value=3, min_value=1, max_value=30)

        if "show_results" not in st.session_state:
            st.session_state.show_results = False

        if st.button("Scrape Jobs"):
            with st.spinner(f"Scraping {role_input} jobs in {location_input} ({days_filter} days ago)..."):
                tavily_response = generateResponse(collection,
                                            f"""
                                        You are given the following inputs:

                                        Skills: {resume_data.get('skills')}
                                        Total experience (years): {resume_experience}
                                        Job role: {role_input}
                                        Location: {location_input}

                                        Task:
                                        Generate a Tavily search query for job searching.

                                        Rules:
                                        1. Output ONLY the search query text. No explanations, no markdown.
                                        2. USE QUOTES for the Job Role and Location to find exact matches. Example: "Python Developer" "Hyderabad"
                                        3. Start with: "<Job role>" jobs in "<Location>"
                                        4. Include experience: "<Total experience> years" or "<Total experience>+ years"
                                        5. CRITICAL: Include the top 3-5 most technical skills from the list.
                                        6. Use Boolean AND/OR logic.
                                        7. Exclude generic terms like "Communication", "Teamwork".
                                        8. Format:
                                           "<Job Role>" jobs "<Location>" "<Experience> years" (<Skill1> OR <Skill2>) (<Skill3> OR <Skill4>)

                                        Example Output:
                                        "Python Developer" jobs "Hyderabad" "3 years experience" (Django OR Flask) (MySQL OR PostgreSQL) AND "Rest API"
                                        
                                        Now generate the robust Tavily query.
                                        """
                                        )
                
                raw_prompt = tavily_response["message"]["content"] if "message" in tavily_response else str(tavily_response)
                
                tavily_prompt = re.sub(r'```(?:python)?\s*|\s*```', '', raw_prompt).strip()
                tavily_prompt = """Python developer jobs in Hyderabad,India.
                    Profile:
                    - 3 years experience
                    - Python, Flask, REST APIs
                    - PostgreSQL, MySQL
                    - Pandas, NumPy
                    - LangChain, RAG, Ollama
                    - JavaScript.
                    Roles:
                    - Python Developer
                    - Backend Python Engineer
                    """
                tavily_prompt = tavily_prompt.replace(" ", "")
                try:
                    domains = st.session_state.domains
                    
                    st.markdown("### Debug Log: Tavily Prompt")
                    with st.expander("Show Generated Search Query"):
                        st.text(tavily_prompt)
                        
                    tavily_result = tavilyclient.tavily_search_jobs(
                        tavily_prompt, 
                        domains, 
                        max_results=int(total_jobs_to_find),
                        days=int(days_filter)
                    )
                    
                    st.markdown(f"### Debug Log: Tavily API Results ({len(tavily_result)} items)")
                    with st.expander("Show Raw API Result Data"):
                        st.json(tavily_result)

                    if tavily_result:
                        structured_data = []
                        
                        stats = {
                            "total_from_tavily": len(tavily_result),
                            "dropped_location_mismatch": 0,
                            "dropped_domain_mismatch": 0,
                            "dropped_bad_url_pattern": 0,
                            "dropped_experience_mismatch": 0,
                            "kept": 0
                        }

                        for r in tavily_result:
                            content = r.get("content", "")
                            title = r.get("title", "")
                            
                            norm_loc = location_input.lower().strip()
                            norm_content = content.lower()
                            norm_title = title.lower()

                            if norm_loc not in norm_content and norm_loc not in norm_title:
                                stats["dropped_location_mismatch"] += 1
                                continue 
                            
                            result_url = r.get("url", "").lower()
                            domain_match = False
                            valid_page_type = True

                            for d in domains:
                                if d.lower() in result_url:
                                    domain_match = True
                                    
                                    if "naukri.com" in d.lower():
                                        if "job-listings-" not in result_url:
                                            valid_page_type = False
                                    
                                    if "linkedin.com" in d.lower():
                                        if "/jobs/search" in result_url or "currentjobid" not in result_url and "/jobs/view" not in result_url:
                                             pass 
                                    break
                            
                            if not domain_match:
                                stats["dropped_domain_mismatch"] += 1
                                continue

                            if not valid_page_type:
                                stats["dropped_bad_url_pattern"] += 1
                                continue
                            found_skills = []
                            for skill in resume_skills:
                                if skill in norm_content or skill in norm_title:
                                    found_skills.append(skill.title())
                            
                            skill_str = ", ".join(found_skills) if found_skills else "See Description"

                            exp_match = re.search(r'(\d+)(\+?|\s*-\s*\d+)\s*years?', content + title, re.IGNORECASE)
                            experience_str = exp_match.group(0) if exp_match else "NA"
                            
                            keep_job = True
                            if experience_str != "NA":
                                try:
                                    nums = re.findall(r'\d+', experience_str)
                                    years = [int(n) for n in nums]
                                    if len(years) == 1:
                                        if resume_experience < years[0]:
                                            keep_job = False
                                    elif len(years) >= 2:
                                        min_exp, max_exp = min(years), max(years)
                                        if not (min_exp <= resume_experience <= max_exp + 2):
                                            keep_job = False
                                except:
                                    pass
                            
                            if not keep_job:
                                stats["dropped_experience_mismatch"] += 1
                                continue
                            
                            stats["kept"] += 1

                            try:
                                domain_name = result_url.split("//")[-1].split("/")[0].replace("www.", "")
                            except:
                                domain_name = "See Link"

                            structured_data.append({
                                "Company Name": domain_name, 
                                "Title": title,
                                "Skill": skill_str,
                                "Link": r.get("url"),
                                "Experience": experience_str,
                                "Description": content
                            })
                        
                        with st.expander("🔍 Show Filter Details (Why did I lose jobs?)"):
                            st.write("We filtered out results that didn't match your strict requirements:")
                            st.json(stats)
                        
                        st.session_state.jobs_df = pd.DataFrame(structured_data)
                        st.session_state.show_results = True
                        st.success(f"Search completed! Found {len(st.session_state.jobs_df)} jobs (Instant View).")

                    else:
                        st.warning("No results found from Tavily.")
                        
                except Exception as e:
                    st.error(f"Error processing jobs: {e}")

        if st.session_state.get("show_results", False) and "jobs_df" in st.session_state:
            jobs_df = st.session_state.jobs_df
            
            if not jobs_df.empty:
                st.info(f"Loaded {len(jobs_df)} jobs. Resume Experience: {resume_experience} years.")
                
                required_cols = ["Company Name", "Title", "Skill", "Link", "Experience", "Description"]
                for col in required_cols:
                    if col not in jobs_df.columns:
                        jobs_df[col] = "NA"

                def calculate_match(row):
                    job_skills_str = str(row["Skill"])
                    
                    if job_skills_str.upper() == "NA":
                         return 0, [], True

                    job_skills = [s.lower().strip() for s in job_skills_str.split(',')]
                    
                    matched_skills = []
                    for rs in resume_skills:
                        for js in job_skills:
                            if rs in js or js in rs:
                                if js not in matched_skills:
                                    matched_skills.append(js)
                    
                    skill_score = len(matched_skills)
                    
                    exp_str = str(row.get("Experience", ""))
                    exp_match = False
                    
                    if "na" in exp_str.lower():
                        exp_match = True
                    else:
                        try:
                            found_nums = re.findall(r'\d+', exp_str)
                            if found_nums:
                                years = [int(n) for n in found_nums]
                                if len(years) == 1:
                                    min_exp = years[0]
                                    max_exp = min_exp + 5
                                elif len(years) >= 2:
                                    min_exp = min(years)
                                    max_exp = max(years)
                                
                                if min_exp <= resume_experience <= max_exp:
                                    exp_match = True
                                elif resume_experience >= min_exp and len(years) == 1: 
                                    exp_match = True
                            else:
                                exp_match = True
                        except:
                            exp_match = True
                    
                    return skill_score, matched_skills, exp_match

                results = jobs_df.apply(calculate_match, axis=1)
                jobs_df["Match Score"] = [res[0] for res in results]
                jobs_df["Matched Skills"] = [res[1] for res in results]
                jobs_df["Exp Match"] = [res[2] for res in results]
                
                filtered_jobs = jobs_df.sort_values(by="Match Score", ascending=False)
                
                st.header(f"Job Results ({len(filtered_jobs)})")
                
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
                    match_color = "green" if row['Match Score'] > 0 else "red"
                    exp_icon = "✅" if row['Exp Match'] else "⚠️"
                    
                    with st.expander(f"{row['Title']} at {row['Company Name']} | Match: {row['Match Score']} | Exp: {row['Experience']} {exp_icon}"):
                        st.markdown(f"**Description:** {row.get('Description', 'NA')}")
                        st.write(f"**Skills:** {row['Skill']}")
                        if row['Matched Skills']:
                            st.write(f"**Matched:** :green[{', '.join(row['Matched Skills'])}]")
                        else:
                            st.write("**Matched:** None")
                            
                        if pd.notna(row['Link']) and row['Link'] != "NA":
                            st.markdown(f"[Apply Now]({row['Link']})")
                        else:
                            st.write("Link not available")
            else:
                 st.warning("No jobs found.")

    except json.JSONDecodeError:
        st.error(f"Failed to parse AI response: {response_text}")
else:
    st.info("Please upload a resume to see job recommendations.")

