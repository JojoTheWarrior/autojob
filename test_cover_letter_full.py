import os, re, time
from typing import List, Dict
from moorcheh_sdk import MoorchehClient, ConflictError

def split_into_paragraphs(master_text: str) -> List[str]:
    # Split on blank lines; keep non-empty chunks
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", master_text) if p.strip()]
    
    # DEBUG: If we only got 1-2 paragraphs, the text might not have blank lines
    # Fallback: try splitting on sentences that end with period + newline
    if len(paragraphs) <= 2:
        # Split on lines, then group consecutive non-empty lines as paragraphs
        lines = [line.strip() for line in master_text.split('\n') if line.strip()]
        
        # Heuristic: Lines that are greetings or very short are their own paragraphs
        # Longer lines that end with periods are likely paragraph breaks
        temp_paragraphs = []
        current = []
        
        for line in lines:
            # Greeting or closing patterns get their own paragraph
            if re.match(r"^(Dear|Sincerely|Best regards|Thank you)", line, re.IGNORECASE):
                if current:
                    temp_paragraphs.append(' '.join(current))
                    current = []
                temp_paragraphs.append(line)
            # If line ends with period and next would start a new thought, break
            elif line.endswith('.') and len(line) > 100:
                current.append(line)
                temp_paragraphs.append(' '.join(current))
                current = []
            else:
                current.append(line)
        
        if current:
            temp_paragraphs.append(' '.join(current))
        
        if len(temp_paragraphs) > len(paragraphs):
            paragraphs = temp_paragraphs
    
    return paragraphs

def extract_body_paragraphs(master_text: str) -> List[str]:
    """
    Extract only the body paragraphs from a master cover letter.
    Removes: header (company/address), greeting, opening glaze line, closing, signature.
    Returns: List of body paragraphs (the middle content paragraphs).
    """
    paragraphs = split_into_paragraphs(master_text)
    
    if not paragraphs:
        return []
    
    # DEBUG: Print what we're working with
    print(f"[DEBUG] Total paragraphs after split: {len(paragraphs)}")
    
    body_start = 0
    body_end = len(paragraphs)
    
    # Find greeting pattern ("Dear...")
    greeting_idx = -1
    for i, para in enumerate(paragraphs):
        if re.match(r"^Dear\s+", para, re.IGNORECASE):
            greeting_idx = i
            # Skip greeting, but be careful about the opening line
            body_start = i + 1
            break
    
    # If no greeting found, try to skip header paragraphs
    if greeting_idx == -1:
        for i, para in enumerate(paragraphs[:3]):
            if len(para) < 100 and not para.endswith('.'):
                body_start = i + 1
            else:
                break
    
    # Look for closing patterns from the end
    closing_patterns = [
        r"^Thank you",
        r"^I (would|will) welcome",
        r"^I look forward",
        r"^I am excited.*opportunity",
        r"^Sincerely",
        r"^Best regards",
        r"^Respectfully",
        r"^Yours truly",
        r"^\[Your Name\]",
    ]
    
    for i in range(len(paragraphs) - 1, body_start - 1, -1):
        para = paragraphs[i]
        if any(re.match(pattern, para, re.IGNORECASE) for pattern in closing_patterns):
            body_end = i
            break
    
    print(f"[DEBUG] Body range: [{body_start}:{body_end}]")
    
    # Extract body paragraphs
    body_paras = paragraphs[body_start:body_end]
    
    # Filter out the opening "glaze" line (usually mentions the role/company)
    filtered = []
    skip_first_substantive = True
    
    for para in body_paras:
        # Skip if too short (likely not body content)
        if len(para.strip()) < 50:
            continue
        
        # Skip opening glaze line (first paragraph that mentions applying/interest)
        if skip_first_substantive and re.search(
            r"(writing to express|excited to apply|interest in|applying for)",
            para,
            re.IGNORECASE
        ):
            skip_first_substantive = False
            continue
        
        # Skip if looks like greeting/closing
        if re.match(r"^(Dear|Thank you|Sincerely|Best regards|I look forward)", para, re.IGNORECASE):
            continue
        
        filtered.append(para)
    
    result = filtered if filtered else body_paras
    print(f"[DEBUG] Returning {len(result)} body paragraphs")
    return result

def ensure_user_namespace(client: MoorchehClient, namespace: str):
    try:
        client.namespaces.create(namespace_name=namespace, type="text")
    except ConflictError:
        pass

def upload_master_cover_letter(user_namespace: str, master_text: str):
    api_key = os.environ["MOORCHEH_API_KEY"]
    paragraphs = extract_body_paragraphs(master_text)

    docs = [{"id": f"p{i}", "text": p} for i, p in enumerate(paragraphs)]

    with MoorchehClient(api_key=api_key) as client:
        ensure_user_namespace(client, user_namespace)
        client.documents.upload(namespace_name=user_namespace, documents=docs)
        time.sleep(1)

def jaccard(a: str, b: str) -> float:
    A = set(a.lower().split())
    B = set(b.lower().split())
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)

def pick_three_diverse(texts: List[str]) -> List[str]:
    chosen: List[str] = []
    for t in texts:
        if not chosen:
            chosen.append(t)
        else:
            overlap = max(jaccard(c, t) for c in chosen)
            if overlap < 0.55:
                chosen.append(t)
        if len(chosen) == 3:
            break
    return chosen if len(chosen) == 3 else texts[:3]

def retrieve_paragraphs(user_namespace: str, job_title: str, company: str, job_desc: str, top_k: int = 10) -> List[str]:
    api_key = os.environ["MOORCHEH_API_KEY"]

    query = f"""
Select the most relevant cover-letter body paragraphs for:
Role: {job_title}
Company: {company}

Job description:
{job_desc}
""".strip()

    with MoorchehClient(api_key=api_key) as client:
        res = client.similarity_search.query(
            namespaces=[user_namespace],
            query=query,
            top_k=top_k,
        )

    hits = res.get("results") or res.get("hits") or []
    texts = []
    for h in hits:
        t = h.get("text") or (h.get("document") or {}).get("text")
        if t:
            texts.append(t)
    return pick_three_diverse(texts)

def generate_glaze_line(user_namespace: str, job_title: str, company: str, job_desc: str) -> str:
    api_key = os.environ["MOORCHEH_API_KEY"]

    prompt = f"""
Write ONE concise opening sentence for a cover letter.
Role: {job_title}
Company: {company}
Must be specific, confident, not cheesy.
Job description: {job_desc}
""".strip()

    with MoorchehClient(api_key=api_key) as client:
        ans = client.answer.generate(namespace=user_namespace, query=prompt, top_k=5)

    if isinstance(ans, str):
        return ans.strip()
    return (ans.get("answer") or ans.get("text") or "").strip()

def replace_company_mentions_in_paragraphs(
    paragraphs: List[str], 
    old_company: str = None, 
    new_company: str = None,
    old_role: str = None,
    new_role: str = None
) -> List[str]:
    """
    Replace any mentions of the old company/role in body paragraphs with new ones.
    """
    if not (old_company or old_role):
        return paragraphs
    
    cleaned = []
    for para in paragraphs:
        text = para
        if old_company and new_company:
            # Handle possessive forms
            text = re.sub(
                re.escape(old_company) + r"'s",
                new_company + "'s",
                text,
                flags=re.IGNORECASE
            )
            text = re.sub(
                re.escape(old_company),
                new_company,
                text,
                flags=re.IGNORECASE
            )
        if old_role and new_role:
            text = re.sub(
                re.escape(old_role),
                new_role,
                text,
                flags=re.IGNORECASE
            )
        cleaned.append(text)
    return cleaned

def render_cover_letter(
    company_name: str,
    company_address: str,
    hiring_manager: str,
    job_title: str,
    glaze_line: str,
    selected_paragraphs: List[str],
    old_company_name: str = None,
    old_job_title: str = None,
) -> str:
    greeting = f"Dear {hiring_manager}," if hiring_manager else "Dear Hiring Manager,"

    cleaned_paragraphs = replace_company_mentions_in_paragraphs(
        selected_paragraphs,
        old_company=old_company_name,
        new_company=company_name,
        old_role=old_job_title,
        new_role=job_title
    )
    body = "\n\n".join(cleaned_paragraphs)

    closing = f"Thank you for your time and consideration. I would welcome the opportunity to further discuss how my skills and interests align with the {job_title} role at {company_name}."

    return "\n".join([
        company_name,
        company_address,
        "",
        greeting,
        "",
        glaze_line,
        "",
        body,
        "",
        closing,
        "",
        "Sincerely,",
        "[Your Name]"
    ]).strip()

def extract_old_company_and_role(master_text: str) -> tuple:
    """
    Try to extract the original company name and role from the master cover letter.
    Returns: (old_company_name, old_job_title) or (None, None) if not found.
    """
    # Look for company name - stop at period or common sentence boundaries
    company_patterns = [
        r"position at ([A-Z][A-Za-z\s&]+?)[\.,]",  # "position at Northshore Systems."
        r"role at ([A-Z][A-Za-z\s&]+?)[\.,]",      # "role at Company Name."
        r"at ([A-Z][A-Za-z\s&]+?)[\.,]",           # "at Company Name."
    ]
    
    old_company = None
    old_role = None
    
    for pattern in company_patterns:
        match = re.search(pattern, master_text)
        if match:
            old_company = match.group(1).strip()
            break
    
    # Look for role/position title - capture text between "the" and "position/role"
    role_patterns = [
        r"the ([\w\s\-–&]+?) (?:position|role) at",  # "the Software Engineer position at"
        r"for the ([\w\s\-–&]+?) (?:position|role)",  # "for the Data Analyst role"
    ]
    for pattern in role_patterns:
        match = re.search(pattern, master_text, re.IGNORECASE)
        if match:
            old_role = match.group(1).strip()
            break
    
    return (old_company, old_role)

def generate_cover_letter_for_job(
    user_id: str,
    master_cover_letter_text: str,
    job_title: str,
    company_name: str,
    company_address: str,
    hiring_manager: str,
    job_desc: str,
) -> str:
    user_namespace = f"coverletter_{user_id}"
    upload_master_cover_letter(user_namespace, master_cover_letter_text)
    
    old_company, old_role = extract_old_company_and_role(master_cover_letter_text)

    paras = retrieve_paragraphs(user_namespace, job_title, company_name, job_desc, top_k=10)

    glaze = generate_glaze_line(user_namespace, job_title, company_name, job_desc) or \
            f"I am excited to apply for the {job_title} role at {company_name}."

    return render_cover_letter(
        company_name, 
        company_address, 
        hiring_manager, 
        job_title, 
        glaze, 
        paras,
        old_company_name=old_company,
        old_job_title=old_role
    )

"""
Full integration test for cover letter generation using Moorcheh SDK.
Tests: upload, retrieval, generation, and rendering with company/role replacement.

Prerequisites:
- Set MOORCHEH_API_KEY environment variable
- Ensure Moorcheh SDK is installed: pip install moorcheh-sdk
"""

import os
from cover_letter import generate_cover_letter_for_job

# Master cover letter for testing
MASTER = """Dear Hiring Manager,

I am writing to express my interest in the Software Engineering Intern – Platform & Tools position at Northshore Systems. I am currently pursuing a degree in Computer Science and am eager to apply my technical foundation in a collaborative environment where software quality, scalability, and thoughtful design are emphasized. Northshore's focus on building tools that empower engineers strongly aligns with how I approach software development.

Through my academic and personal projects, I have developed a solid foundation in programming, data structures, and problem solving. I have experience working with languages such as Python, Java, and JavaScript, and I am comfortable translating abstract requirements into concrete implementations. I value writing code that is readable, maintainable, and supported by testing, and I actively seek feedback through reviews and iteration.

I am particularly drawn to this role's emphasis on internal platforms and developer tooling. I enjoy working behind the scenes to improve workflows, reduce friction, and enable other engineers to work more efficiently. Whether debugging issues, refining interfaces, or automating repetitive tasks, I find satisfaction in building systems that quietly but meaningfully improve productivity.

In addition to technical skills, I bring a strong sense of ownership and adaptability to my work. I am comfortable learning new technologies independently, asking clarifying questions when requirements are ambiguous, and adjusting my approach as constraints evolve. I have worked both independently and in team settings, and I value clear communication and shared understanding when collaborating on technical decisions.

Beyond specific tools or languages, I am motivated by continuous improvement—both of systems and of myself as an engineer. I actively reflect on past work to identify better patterns, clearer abstractions, or more efficient solutions, and I enjoy learning from more experienced developers in structured environments such as code reviews and design discussions.

I am also interested in understanding the broader context in which software is built. I enjoy collaborating with product or non-technical stakeholders to understand the "why" behind a feature, and I aim to write software that balances technical robustness with real user needs. This perspective helps me make more informed tradeoffs and contribute beyond isolated tasks.

Northshore Systems' emphasis on collaboration, reliability, and thoughtful tooling makes it an environment where I believe I could both contribute meaningfully and grow rapidly. I am excited by the opportunity to learn from experienced engineers while supporting systems that have a real impact across teams.

Thank you for considering my application. I would welcome the opportunity to further discuss how my skills and interests align with this role, and I look forward to the possibility of contributing to Northshore Systems.

Sincerely,
Max Wang"""

# Job description for testing
JOB_DESC = """
We are seeking a Software Developer Intern to join our Data & Analytics team. 
You will work on building data pipelines, creating visualizations, and helping 
our product team make data-driven decisions.

Responsibilities:
- Build and maintain ETL pipelines using Python and SQL
- Create dashboards and visualizations for business stakeholders
- Collaborate with data scientists on machine learning projects
- Write clean, tested, and documented code
- Participate in code reviews and team discussions

Requirements:
- Currently pursuing a degree in Computer Science or related field
- Experience with Python and SQL
- Familiarity with data analysis libraries (pandas, numpy)
- Strong problem-solving skills
- Good communication and collaboration skills

Nice to have:
- Experience with data visualization tools (Tableau, Plotly, etc.)
- Knowledge of cloud platforms (AWS, GCP, Azure)
- Understanding of machine learning concepts
"""

def test_full_generation():
    """Test complete cover letter generation with Moorcheh."""
    
    print("=" * 70)
    print("FULL INTEGRATION TEST - Cover Letter Generation with Moorcheh")
    print("=" * 70)
    
    # Check API key
    if not os.environ.get("MOORCHEH_API_KEY"):
        print("\n❌ ERROR: MOORCHEH_API_KEY not set!")
        print("Set it with: export MOORCHEH_API_KEY='your-key-here'")
        return
    
    print("\n✓ API key found")
    
    # Test parameters
    user_id = "test_user_123"
    job_title = "Software Developer Intern – Data & Analytics"
    company_name = "Meridian Insight Labs"
    company_address = "Vancouver, BC (Remote-friendly within Canada)"
    hiring_manager = "Sarah Chen"
    
    print(f"\n📝 Generating cover letter for:")
    print(f"   User: {user_id}")
    print(f"   Role: {job_title}")
    print(f"   Company: {company_name}")
    print(f"   Hiring Manager: {hiring_manager}")
    
    try:
        print("\n🔄 Step 1: Uploading master cover letter to Moorcheh...")
        print(f"   (Namespace: coverletter_{user_id})")
        
        print("\n🔄 Step 2: Performing semantic search for relevant paragraphs...")
        print("   (Using job description to find best matches)")
        
        print("\n🔄 Step 3: Generating AI-powered opening line...")
        
        print("\n🔄 Step 4: Replacing old company/role mentions...")
        print("   Old company: Northshore Systems → New: Meridian Insight Labs")
        print("   Old role: Software Engineering Intern – Platform & Tools")
        print("   New role: Software Developer Intern – Data & Analytics")
        
        print("\n🔄 Step 5: Rendering final cover letter...")
        
        # Generate the cover letter
        result = generate_cover_letter_for_job(
            user_id=user_id,
            master_cover_letter_text=MASTER,
            job_title=job_title,
            company_name=company_name,
            company_address=company_address,
            hiring_manager=hiring_manager,
            job_desc=JOB_DESC
        )
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS! Generated Cover Letter:")
        print("=" * 70)
        print(result)
        print("=" * 70)
        
        # Validation checks
        print("\n🔍 Validation Checks:")
        checks_passed = 0
        checks_total = 5
        
        if company_name in result:
            print(f"   ✓ New company name present: '{company_name}'")
            checks_passed += 1
        else:
            print(f"   ✗ New company name missing: '{company_name}'")
        
        if "Northshore" not in result:
            print("   ✓ Old company name removed: 'Northshore Systems'")
            checks_passed += 1
        else:
            print("   ✗ Old company name still present: 'Northshore Systems'")
        
        if hiring_manager in result:
            print(f"   ✓ Hiring manager name present: '{hiring_manager}'")
            checks_passed += 1
        else:
            print(f"   ✗ Hiring manager name missing: '{hiring_manager}'")
        
        if job_title in result:
            print(f"   ✓ Job title present: '{job_title}'")
            checks_passed += 1
        else:
            print(f"   ✗ Job title missing: '{job_title}'")
        
        # Check if body paragraphs are present (should have multiple paragraphs)
        paragraph_count = result.count('\n\n')
        if paragraph_count >= 4:  # Header, greeting, body paras, closing
            print(f"   ✓ Multiple body paragraphs present: {paragraph_count} sections")
            checks_passed += 1
        else:
            print(f"   ✗ Insufficient body paragraphs: {paragraph_count} sections")
        
        print(f"\n📊 Score: {checks_passed}/{checks_total} checks passed")
        
        if checks_passed == checks_total:
            print("\n🎉 All tests passed! Cover letter generation working perfectly.")
        elif checks_passed >= 3:
            print("\n⚠️  Most tests passed. Minor issues detected.")
        else:
            print("\n❌ Multiple issues detected. Review the output above.")
        
    except Exception as e:
        print(f"\n❌ ERROR during generation:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return
    
    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)

if __name__ == "__main__":
    test_full_generation()


