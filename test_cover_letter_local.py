from cover_letter import (
    extract_body_paragraphs,
    extract_old_company_and_role,
    render_cover_letter
)

MASTER = """Dear Hiring Manager,
I am writing to express my interest in the Software Engineering Intern – Platform & Tools position at Northshore Systems. I am currently pursuing a degree in Computer Science and am eager to apply my technical foundation in a collaborative environment where software quality, scalability, and thoughtful design are emphasized. Northshore’s focus on building tools that empower engineers strongly aligns with how I approach software development.
Through my academic and personal projects, I have developed a solid foundation in programming, data structures, and problem solving. I have experience working with languages such as Python, Java, and JavaScript, and I am comfortable translating abstract requirements into concrete implementations. I value writing code that is readable, maintainable, and supported by testing, and I actively seek feedback through reviews and iteration.
I am particularly drawn to this role’s emphasis on internal platforms and developer tooling. I enjoy working behind the scenes to improve workflows, reduce friction, and enable other engineers to work more efficiently. Whether debugging issues, refining interfaces, or automating repetitive tasks, I find satisfaction in building systems that quietly but meaningfully improve productivity.
In addition to technical skills, I bring a strong sense of ownership and adaptability to my work. I am comfortable learning new technologies independently, asking clarifying questions when requirements are ambiguous, and adjusting my approach as constraints evolve. I have worked both independently and in team settings, and I value clear communication and shared understanding when collaborating on technical decisions.
Beyond specific tools or languages, I am motivated by continuous improvement—both of systems and of myself as an engineer. I actively reflect on past work to identify better patterns, clearer abstractions, or more efficient solutions, and I enjoy learning from more experienced developers in structured environments such as code reviews and design discussions.
I am also interested in understanding the broader context in which software is built. I enjoy collaborating with product or non-technical stakeholders to understand the “why” behind a feature, and I aim to write software that balances technical robustness with real user needs. This perspective helps me make more informed tradeoffs and contribute beyond isolated tasks.
Northshore Systems’ emphasis on collaboration, reliability, and thoughtful tooling makes it an environment where I believe I could both contribute meaningfully and grow rapidly. I am excited by the opportunity to learn from experienced engineers while supporting systems that have a real impact across teams.
Thank you for considering my application. I would welcome the opportunity to further discuss how my skills and interests align with this role, and I look forward to the possibility of contributing to Northshore Systems.
Sincerely,
Max Wang"""

if __name__ == "__main__":
    body = extract_body_paragraphs(MASTER)
    old_company, old_role = extract_old_company_and_role(MASTER)

    print("---- BODY PARAGRAPHS ----")
    for i, p in enumerate(body):
        print(f"\n[{i}]\n{p}\n")

    print("---- RENDERED LETTER ----")
    print(
        render_cover_letter(
            company_name="Meridian Insight Labs",
            company_address="Vancouver, BC (Remote-friendly within Canada)",
            hiring_manager="Hiring Manager",
            job_title="Software Developer Intern – Data & Analytics",
            glaze_line="I am excited to apply for the Software Developer Intern role at Meridian Insight Labs.",
            selected_paragraphs=body[:3],
            old_company_name=old_company,
            old_job_title=old_role,
        )
    )
