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
    print(f"[DEBUG] Retrieved {len(hits)} hits from Moorcheh")  # ADD THIS
    texts = []
    for h in hits:
        t = h.get("text") or (h.get("document") or {}).get("text")
        if t:
            texts.append(t)
    print(f"[DEBUG] Extracted {len(texts)} text paragraphs")  # ADD THIS
    result = pick_three_diverse(texts)
    print(f"[DEBUG] After diversity filter: {len(result)} paragraphs")  # ADD THIS
    return result

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
        r"position at ([A-Z][A-Za-z\s&]+?)[\.,]",
        r"role at ([A-Z][A-Za-z\s&]+?)[\.,]",
        r"at ([A-Z][A-Za-z\s&]+?)[\.,]",
    ]
    
    old_company = None
    old_role = None
    
    for pattern in company_patterns:
        match = re.search(pattern, master_text)
        if match:
            old_company = match.group(1).strip()
            break
    
    # Look for role/position title
    role_patterns = [
        r"the ([\w\s\-–&]+?) (?:position|role) at",
        r"for the ([\w\s\-–&]+?) (?:position|role)",
    ]
    for pattern in role_patterns:
        match = re.search(pattern, master_text, re.IGNORECASE)
        if match:
            old_role = match.group(1).strip()
            break
    
    return (old_company, old_role)

def extract_job_details(job_desc: str) -> dict:
    """
    Extract job title, company name, and location from job description.
    Returns: dict with 'title', 'company', 'location'
    """
    details = {
        'title': None,
        'company': None,
        'location': None
    }
    
    # Company patterns
    company_patterns = [
        r"(?:Company|Organization):\s*([A-Z][A-Za-z\s&.,]+?)(?:\n|$)",
        r"(?:at|@)\s+([A-Z][A-Za-z\s&]+?)(?:\n|\s+is|\s+seeks)",
        r"^([A-Z][A-Za-z\s&]+?)\s+is (?:seeking|hiring|looking for)",
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, job_desc, re.MULTILINE)
        if match:
            details['company'] = match.group(1).strip()
            break
    
    # Job title patterns
    title_patterns = [
        r"(?:Position|Role|Title):\s*([A-Za-z\s\-–&/]+?)(?:\n|$)",
        r"(?:seeking|hiring|for)\s+(?:a|an)\s+([A-Za-z\s\-–&/]+?)\s+(?:to|for|who)",
        r"^([A-Za-z\s\-–&/]+?)\s*(?:\n|$)",
    ]
    
    for pattern in title_patterns:
        match = re.search(pattern, job_desc, re.MULTILINE)
        if match:
            title = match.group(1).strip()
            if len(title) > 5 and not title.lower().startswith(('we are', 'join', 'about')):
                details['title'] = title
                break
    
    # Location patterns
    location_patterns = [
        r"Location:\s*([A-Za-z\s,\-()]+?)(?:\n|$)",
        r"(?:in|at)\s+([A-Z][a-z]+,\s*[A-Z]{2}(?:\s*\([^)]+\))?)",
        r"(?:Remote|Hybrid|On-site).*?(?:in|from)\s+([A-Za-z\s,\-]+?)(?:\n|$)",
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, job_desc, re.MULTILINE | re.IGNORECASE)
        if match:
            details['location'] = match.group(1).strip()
            break
    
    # Defaults if extraction fails
    if not details['company']:
        details['company'] = "the Company"
    if not details['title']:
        details['title'] = "this position"
    if not details['location']:
        details['location'] = "Remote"
    
    return details

def generate_cover_letter_for_job(
    user_id: str,
    master_cover_letter_text: str,
    job_desc: str,
) -> str:
    """
    Generate a customized cover letter from a master template and job description.
    Automatically extracts job title, company name, and location from the job description.
    
    Args:
        user_id: Unique identifier for the user
        master_cover_letter_text: The user's master cover letter template
        job_desc: The full job description text
    
    Returns:
        Formatted cover letter as a string
    """
    user_namespace = f"coverletter_{user_id}"
    
    # Extract job details from description
    job_details = extract_job_details(job_desc)
    job_title = job_details['title']
    company_name = job_details['company']
    company_address = job_details['location']
    
    upload_master_cover_letter(user_namespace, master_cover_letter_text)
    
    old_company, old_role = extract_old_company_and_role(master_cover_letter_text)

    paras = retrieve_paragraphs(user_namespace, job_title, company_name, job_desc, top_k=10)

    glaze = generate_glaze_line(user_namespace, job_title, company_name, job_desc) or \
            f"I am excited to apply for the {job_title} role at {company_name}."

    return render_cover_letter(
        company_name, 
        company_address, 
        hiring_manager="Hiring Manager",
        job_title=job_title, 
        glaze_line=glaze, 
        selected_paragraphs=paras,
        old_company_name=old_company,
        old_job_title=old_role
    )

