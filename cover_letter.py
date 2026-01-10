import os, re, time
from typing import List, Dict
from moorcheh_sdk import MoorchehClient, ConflictError

def split_into_paragraphs(master_text: str) -> List[str]:
    # Split on blank lines; keep non-empty chunks
    return [p.strip() for p in re.split(r"\n\s*\n+", master_text) if p.strip()]

def extract_body_paragraphs(master_text: str) -> List[str]:
    """
    Extract only the body paragraphs from a master cover letter.
    Removes: header (company/address), greeting, opening glaze line, closing, signature.
    Returns: List of body paragraphs (the middle content paragraphs).
    """
    # Split into paragraphs
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
            # Skip greeting and the opening glaze (first paragraph after greeting)
            body_start = i + 2  # Skip greeting + opening glaze paragraph
            break
    
    # If no greeting found, try to skip header paragraphs (usually first 1-3 are header/address)
    if greeting_idx == -1:
        # Skip potential header (short lines that might be company/address)
        for i, para in enumerate(paragraphs[:3]):
            if len(para) < 100 and not para.endswith('.'):
                body_start = i + 1
            else:
                break
        # Also skip first substantive paragraph as it's likely the opening glaze
        body_start = max(body_start, 1)
    
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
    
    # Filter: remove very short paragraphs or those that look like greetings/closings
    filtered = []
    for para in body_paras:
        # Skip if too short (likely not body content)
        if len(para.strip()) < 50:
            continue
        # Skip if looks like greeting/closing
        if re.match(r"^(Dear|Thank you|Sincerely|Best regards|I look forward)", para, re.IGNORECASE):
            continue
        filtered.append(para)
    
    return filtered if filtered else body_paras  # Fallback to original if filter too aggressive

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

        # Optional: if SDK supports delete/overwrite, use it here to avoid duplicates.
        # Hackathon-safe approach: re-upload with same IDs p0..pn (overwrites if supported).
        client.documents.upload(namespace_name=user_namespace, documents=docs)

        # Small delay to allow indexing in demo settings
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

    # Response shape can vary; adapt after one print() in your environment.
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

    # If ans is a dict, pull the string; adjust based on real output
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
    This ensures paragraphs from the master letter don't reference old companies.
    """
    if not (old_company or old_role):
        return paragraphs
    
    cleaned = []
    for para in paragraphs:
        text = para
        # Replace company mentions (case-insensitive)
        if old_company and new_company:
            # Handle possessive forms (e.g., "Northshore's" -> "Meridian Insight Labs'")
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
        # Replace role mentions
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
    # Simple deterministic template; replace with Jinja2 if you want.
    greeting = f"Dear {hiring_manager}," if hiring_manager else "Dear Hiring Manager,"

    # Replace any old company/role mentions in paragraphs with new ones
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
    # Look for patterns like "I am writing to express my interest in the [ROLE] position at [COMPANY]"
    # or "I am excited to apply for the [ROLE] role at [COMPANY]"
    patterns = [
        r"position at ([^,.\n]+)",
        r"role at ([^,.\n]+)",
        r"at ([^,.\n]+)",
    ]
    
    old_company = None
    old_role = None
    
    # Try to find company name in opening
    for pattern in patterns:
        match = re.search(pattern, master_text, re.IGNORECASE)
        if match:
            old_company = match.group(1).strip()
            break
    
    # Try to find role in opening (between "the" and "position/role")
    role_patterns = [
        r"the ([^,]+) (?:position|role)",
        r"for the ([^,]+) (?:position|role)",
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
    # 1) per-user namespace
    user_namespace = f"coverletter_{user_id}"

    # 2) ensure uploaded (in production you'd do this only if not already done / changed)
    upload_master_cover_letter(user_namespace, master_cover_letter_text)
    
    # 2.5) Extract old company/role from master text for replacement
    old_company, old_role = extract_old_company_and_role(master_cover_letter_text)

    # 3) retrieve best 3 paragraphs via Moorcheh
    paras = retrieve_paragraphs(user_namespace, job_title, company_name, job_desc, top_k=10)

    # 4) optional: glaze line via Moorcheh answer
    glaze = generate_glaze_line(user_namespace, job_title, company_name, job_desc) or \
            f"I am excited to apply for the {job_title} role at {company_name}."

    # 5) template render (with company/role replacement)
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





