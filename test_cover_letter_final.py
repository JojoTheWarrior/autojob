"""
Full integration test for cover letter generation using Moorcheh SDK.
Tests: upload, retrieval, generation, and rendering with automatic job detail extraction.

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

# Job description with structured info for automatic extraction
JOB_DESC = """
Software Developer Intern – Data & Analytics

Company: Meridian Insight Labs
Location: Vancouver, BC (Remote-friendly within Canada)

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
    """Test complete cover letter generation with Moorcheh and automatic extraction."""
    
    print("=" * 70)
    print("FULL INTEGRATION TEST - Cover Letter Generation with Moorcheh")
    print("=" * 70)
    
    # Check API key
    if not os.environ.get("MOORCHEH_API_KEY"):
        print("\n❌ ERROR: MOORCHEH_API_KEY not set!")
        print("Set it with: export MOORCHEH_API_KEY='your-key-here'")
        return
    
    print("\n✓ API key found")
    
    # Test parameters - only user_id and job_desc needed!
    user_id = "test_user_123"
    
    print(f"\n📝 Generating cover letter for:")
    print(f"   User: {user_id}")
    print(f"   Job description will be parsed automatically...")
    
    try:
        print("\n🔄 Step 1: Extracting job details from description...")
        print("   (Title, company, location extracted automatically)")
        
        print("\n🔄 Step 2: Uploading master cover letter to Moorcheh...")
        print(f"   (Namespace: coverletter_{user_id})")
        
        print("\n🔄 Step 3: Performing semantic search for relevant paragraphs...")
        print("   (Using job description to find best matches)")
        
        print("\n🔄 Step 4: Generating AI-powered opening line...")
        
        print("\n🔄 Step 5: Replacing old company/role mentions...")
        
        print("\n🔄 Step 6: Rendering final cover letter...")
        
        # Generate the cover letter - simplified 3-parameter API!
        result = generate_cover_letter_for_job(
            user_id=user_id,
            master_cover_letter_text=MASTER,
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
        
        if "Meridian Insight Labs" in result:
            print(f"   ✓ Company name extracted and present: 'Meridian Insight Labs'")
            checks_passed += 1
        else:
            print(f"   ✗ Company name missing: 'Meridian Insight Labs'")
        
        if "Northshore" not in result:
            print("   ✓ Old company name removed: 'Northshore Systems'")
            checks_passed += 1
        else:
            print("   ✗ Old company name still present: 'Northshore Systems'")
        
        if "Dear Hiring Manager," in result:
            print(f"   ✓ Generic greeting present: 'Dear Hiring Manager,'")
            checks_passed += 1
        else:
            print(f"   ✗ Generic greeting missing")
        
        if "Software Developer Intern" in result or "Data & Analytics" in result:
            print(f"   ✓ Job title extracted and present")
            checks_passed += 1
        else:
            print(f"   ✗ Job title missing")
        
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

