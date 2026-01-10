import os, re, time
from typing import List, Dict
from moorcheh_sdk import MoorchehClient, ConflictError

def split_into_paragraphs(master_text: str) -> List[str]:
    # Split on blank lines; keep non-empty chunks
    return [p.strip() for p in re.split(r"\n\s*\n+", master_text) if p.strip()]

def ensure_user_namespace(client: MoorchehClient, namespace: str):
    try:
        client.namespaces.create(namespace_name=namespace, type="text")
    except ConflictError:
        pass

def upload_master_cover_letter(user_namespace: str, master_text: str):
    api_key = os.environ["MOORCHEH_API_KEY"]
    paragraphs = split_into_paragraphs(master_text)

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

def render_cover_letter(
    company_name: str,
    company_address: str,
    hiring_manager: str,
    job_title: str,
    glaze_line: str,
    selected_paragraphs: List[str],
) -> str:
    # Simple deterministic template; replace with Jinja2 if you want.
    greeting = f"Dear {hiring_manager}," if hiring_manager else "Dear Hiring Manager,"

    body = "\n\n".join(selected_paragraphs)

    closing = f"Thank you for your time and consideration. I’d welcome the opportunity to further discuss my fit for the {job_title} role at {company_name}."

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

    # 2) ensure uploaded (in production you’d do this only if not already done / changed)
    upload_master_cover_letter(user_namespace, master_cover_letter_text)

    # 3) retrieve best 3 paragraphs via Moorcheh
    paras = retrieve_paragraphs(user_namespace, job_title, company_name, job_desc, top_k=10)

    # 4) optional: glaze line via Moorcheh answer
    glaze = generate_glaze_line(user_namespace, job_title, company_name, job_desc) or \
            f"I am excited to apply for the {job_title} role at {company_name}."

    # 5) template render
    return render_cover_letter(company_name, company_address, hiring_manager, job_title, glaze, paras)





