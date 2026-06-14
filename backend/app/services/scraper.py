import httpx
from bs4 import BeautifulSoup
from app.core.database import schemes_collection
import datetime
import json
import re

# High-quality seed data as a robust local backup
SEED_SCHEMES = [
    {
        "id": "pm_kisan_2026",
        "title": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "description": "An initiative by the Government of India that provides up to ₹6,000 per year in three equal installments to small and marginal farmer families.",
        "eligibility_criteria": {
            "occupation": ["Farmer", "Agriculture"],
            "annual_income_limit": 200000,
            "caste_category": ["All"],
            "state": ["All"],
            "gender": ["Male", "Female", "Other"]
        },
        "benefits": "₹6,000 per year, paid in three equal installments of ₹2,000 directly into the bank accounts of the farmers.",
        "required_documents": ["Aadhaar Card", "Landholding Papers", "Bank Account Details", "Mobile Number"],
        "application_deadline": "Open Year-Round",
        "source_url": "https://pmkisan.gov.in/"
    },
    {
        "id": "post_matric_sc_2026",
        "title": "Post Matric Scholarship Scheme for SC Students",
        "description": "A centrally sponsored scheme that provides financial assistance to Scheduled Caste students studying at post-matriculation or post-secondary stages.",
        "eligibility_criteria": {
            "education": ["11th", "12th", "Undergraduate", "Postgraduate", "Diploma", "JEE"],
            "caste_category": ["SC"],
            "annual_income_limit": 250000,
            "state": ["All"],
            "gender": ["Male", "Female", "Other"]
        },
        "benefits": "100% compulsory non-refundable fees reimbursement and a monthly maintenance allowance up to ₹1,200 depending on the course group.",
        "required_documents": ["Caste Certificate", "Income Certificate", "Aadhaar Card", "Previous Class Marksheet", "Fee Receipt", "Bank Passbook"],
        "application_deadline": "31st December 2026",
        "source_url": "https://scholarships.gov.in/"
    },
    {
        "id": "up_post_matric_obc_2026",
        "title": "Uttar Pradesh Post Matric Scholarship for OBC Students",
        "description": "Scholarship and fee reimbursement scheme by the Government of Uttar Pradesh for Other Backward Classes (OBC) students pursuing higher education, engineering, or competitive exam preparation (like JEE).",
        "eligibility_criteria": {
            "state": ["Uttar Pradesh", "UP"],
            "caste_category": ["OBC", "Other Backward Classes"],
            "annual_income_limit": 200000,
            "education": ["11th", "12th", "Undergraduate", "Postgraduate", "JEE", "Engineering"],
            "gender": ["Male", "Female", "Other"]
        },
        "benefits": "Complete tuition fee reimbursement and a monthly maintenance allowance up to ₹1,000.",
        "required_documents": ["UP Domicile Certificate", "OBC Caste Certificate", "Income Certificate", "Aadhaar Card", "Fee Receipt", "College ID"],
        "application_deadline": "30th November 2026",
        "source_url": "https://scholarship.up.gov.in/"
    },
    {
        "id": "national_handicapped_finance_2026",
        "title": "National Scholarship for Students with Disabilities",
        "description": "Financial assistance for students with physical disabilities (40% or more) to pursue professional or technical courses.",
        "eligibility_criteria": {
            "disability_status": ["Handicapped", "Disabled", "Physically Handicapped", "Yes"],
            "annual_income_limit": 300000,
            "education": ["Undergraduate", "Postgraduate", "Diploma", "JEE", "Engineering"],
            "caste_category": ["All"],
            "state": ["All"],
            "gender": ["Male", "Female", "Other"]
        },
        "benefits": "Reimbursement of tuition fees up to ₹50,000 per year and maintenance allowance of ₹2,500/month.",
        "required_documents": ["Disability Certificate", "Aadhaar Card", "Income Certificate", "Marksheet of qualifying exam"],
        "application_deadline": "31st October 2026",
        "source_url": "https://www.nhfdc.nic.in/"
    },
    {
        "id": "telangana_rythu_bandhu_2026",
        "title": "Telangana Rythu Bandhu Scheme",
        "description": "A welfare program to support farmer's investment for two crops a year by the Government of Telangana.",
        "eligibility_criteria": {
            "occupation": ["Farmer", "Agriculture"],
            "state": ["Telangana"],
            "caste_category": ["All"],
            "annual_income_limit": 500000,
            "gender": ["Male", "Female", "Other"]
        },
        "benefits": "Financial support of ₹5,000 per acre per season to purchase inputs like seeds, fertilizers, and pesticides.",
        "required_documents": ["Pattadar Passbook", "Aadhaar Card", "Bank Account Details"],
        "application_deadline": "Open Seasonal",
        "source_url": "https://rythubandhu.telangana.gov.in/"
    },
    {
        "id": "karnataka_vidyasiri_2026",
        "title": "Karnataka Vidyasiri Scholarship (Food & Accommodation)",
        "description": "Welfare scheme by the Government of Karnataka offering financial aid to backward classes (OBC) and SC/ST students studying in post-matric courses.",
        "eligibility_criteria": {
            "state": ["Karnataka"],
            "caste_category": ["OBC", "SC", "ST"],
            "annual_income_limit": 250000,
            "education": ["Undergraduate", "Postgraduate", "Diploma", "B.Tech"],
            "gender": ["Male", "Female", "Other"]
        },
        "benefits": "₹1,500 per month for food and accommodation assistance for 10 months.",
        "required_documents": ["Karnataka Domicile Certificate", "Caste Certificate", "Income Certificate", "Marksheet", "College Admission Proof"],
        "application_deadline": "31st October 2026",
        "source_url": "https://ssp.postmatric.karnataka.gov.in/"
    },
    {
        "id": "ap_amma_vodi_2026",
        "title": "Andhra Pradesh Jagananna Amma Vodi",
        "description": "Financial assistance program by the Government of Andhra Pradesh for mothers or guardians from low-income families to support their children's school education.",
        "eligibility_criteria": {
            "state": ["Andhra Pradesh"],
            "annual_income_limit": 150000,
            "education": ["1st to 12th", "Secondary", "11th", "12th"],
            "caste_category": ["All"],
            "gender": ["Female", "Male"]
        },
        "benefits": "Annual financial assistance of ₹15,000 deposited directly into the mother's verified bank account.",
        "required_documents": ["Aadhaar Card of Child & Mother", "Ration Card (White)", "School ID/Proof of Study", "Bank Account Passbook"],
        "application_deadline": "30th June 2026",
        "source_url": "https://jaganannaammavodi.ap.gov.in/"
    },
    {
        "id": "national_merit_scholarship_2026",
        "title": "National Means-Cum-Merit Scholarship Scheme (NMMSS)",
        "description": "Central government scholarship to award scholarships to meritorious students of economically weaker sections to arrest their drop-out at class VIII.",
        "eligibility_criteria": {
            "education": ["9th", "10th", "11th", "12th", "Secondary"],
            "annual_income_limit": 350000,
            "state": ["All"],
            "caste_category": ["All"],
            "gender": ["Male", "Female", "Other"]
        },
        "benefits": "Scholarship of ₹12,000 per annum (₹1,000 per month) to selected students studying in state government/aided schools.",
        "required_documents": ["Class 8 Marksheet", "Income Certificate", "Caste Certificate (if applicable)", "Aadhaar Card", "School Verification Certificate"],
        "application_deadline": "15th November 2026",
        "source_url": "https://scholarships.gov.in/"
    },
    {
        "id": "pm_shram_yogi_2026",
        "title": "Pradhan Mantri Shram Yogi Maan-dhan (PM-SYM)",
        "description": "A voluntary and contributory pension scheme for unorganised workers like street vendors, mid-day meal workers, brick kiln workers, ragpickers, and domestic workers.",
        "eligibility_criteria": {
            "occupation": ["Unorganised Worker", "Labourer", "Driver", "Domestic Worker", "Street Vendor"],
            "annual_income_limit": 180000,
            "state": ["All"],
            "caste_category": ["All"],
            "gender": ["Male", "Female", "Other"]
        },
        "benefits": "Assured minimum monthly pension of ₹3,000 after attaining the age of 60 years.",
        "required_documents": ["Aadhaar Card", "Savings Bank Account / Jan Dhan Account with IFSC", "Mobile Number"],
        "application_deadline": "Open Year-Round",
        "source_url": "https://maandhan.in/"
    }
]

async def scrape_buddy_for_study():
    """
    Performs real live web scraping of active scholarships listed on Buddy4Study's main page.
    Falls back gracefully if Cloudflare / DDOS protection blocks the request.
    """
    url = "https://www.buddy4study.com/scholarships"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    
    scraped_data = []
    print("Connecting to Buddy4Study.com for scraping...")
    
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                print("HTML content fetched successfully. Parsing...")
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Buddy4Study lists scholarships inside article cards
                # They use article tags, class names like .scholarship-card or lists with structured details
                scholarships = soup.find_all("article") or soup.select(".scholarshipslist") or soup.select(".card")
                print(f"Detected {len(scholarships)} raw layout nodes on the page.")
                
                for idx, item in enumerate(scholarships[:6]):
                    # 1. Extract Title
                    title_tag = item.find("h2") or item.find("h3") or item.select_one(".title") or item.select_one(".heading")
                    if not title_tag:
                        continue
                    title = title_tag.get_text().strip()
                    
                    # 2. Extract Description/Eligibility snippet
                    desc_tag = item.find("p") or item.select_one(".description") or item.select_one(".summary")
                    desc = desc_tag.get_text().strip() if desc_tag else "Active scholarship program listed on Buddy4Study."
                    
                    # Clean up title and remove extra spaces
                    title = re.sub(r'\s+', ' ', title)
                    desc = re.sub(r'\s+', ' ', desc)

                    # 3. Try to extract Deadline details
                    deadline = "TBD"
                    deadline_tag = item.find(text=re.compile(r'Deadline|Last Date|Expiry', re.I)) or item.select_one(".deadline")
                    if deadline_tag:
                        deadline = deadline_tag.get_text().strip()
                    
                    # Parse eligibility rules from the description using simple regex
                    income_limit = 250000
                    income_match = re.search(r'(?:income|income limit|INR)\s*(?:is\s*less\s*than|below|under)?\s*(?:Rs\.?|₹)?\s*([\d,]+)', desc, re.I)
                    if income_match:
                        try:
                            val = income_match.group(1).replace(',', '')
                            income_limit = int(val)
                        except ValueError:
                            pass
                            
                    education = ["Undergraduate", "Postgraduate", "11th", "12th"]
                    if "school" in desc.lower() or "class" in desc.lower():
                        education.extend(["9th", "10th"])
                    if "college" in desc.lower() or "degree" in desc.lower():
                        education.extend(["Undergraduate", "Postgraduate", "Diploma"])
                    
                    # Create the structured object
                    link = url
                    link_tag = item.find("a", href=True)
                    if link_tag:
                        href = link_tag["href"]
                        if href.startswith("/"):
                            link = f"https://www.buddy4study.com{href}"
                        elif href.startswith("http"):
                            link = href
                            
                    scraped_data.append({
                        "title": title,
                        "description": desc,
                        "eligibility_criteria": {
                            "education": list(set(education)),
                            "annual_income_limit": income_limit,
                            "caste_category": ["All"],
                            "state": ["All"],
                            "gender": ["Male", "Female", "Other"]
                        },
                        "benefits": "Financial assistance as per official guidelines on the portal.",
                        "required_documents": ["Previous class marksheet", "Income certificate", "Aadhaar Card", "Admission proof"],
                        "application_deadline": deadline,
                        "source_url": link
                    })
                
                print(f"Scraped {len(scraped_data)} scholarships from Buddy4Study.")
            else:
                print(f"Buddy4Study returned response code {response.status_code} (Cloudflare block). Using local seed backup.")
    except Exception as e:
        print(f"Web scraper connection error: {e}. Defaulting to pre-seeded backup list.")
        
    return scraped_data

async def seed_all_schemes():
    """
    Combines the static seed catalog and any live scraped scholarships from Buddy4Study,
    upserting them into MongoDB.
    """
    # 1. Start with backup list
    all_schemes = list(SEED_SCHEMES)
    
    # 2. Scrape live data
    scraped = await scrape_buddy_for_study()
    for s in scraped:
        # Avoid duplicate titles
        if not any(x["title"].lower() == s["title"].lower() for x in all_schemes):
            slug = re.sub(r'[^a-z0-9_]', '', s["title"].lower().replace(" ", "_"))[:50]
            s["id"] = f"scraped_{slug}"
            all_schemes.append(s)
            
    # 3. Upsert into MongoDB
    inserted = 0
    for scheme in all_schemes:
        result = await schemes_collection.update_one(
            {"title": scheme["title"]},
            {"$set": {
                **scheme,
                "updated_at": datetime.datetime.utcnow()
            }},
            upsert=True
        )
        if result.upserted_id or result.modified_count > 0:
            inserted += 1
            
    print(f"Database sync complete: Loaded {len(all_schemes)} total schemes.")
    return len(all_schemes)
