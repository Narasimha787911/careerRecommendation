import os
import pandas as pd
import logging
import json

logging.basicConfig(level=logging.INFO)

def create_sample_career_dataset():
    """
    Creates a sample career recommendation dataset based on the structure of
    the Kaggle 'Career Recommendation Dataset' by Breejeshdhar
    https://www.kaggle.com/datasets/breejeshdhar/career-recommendation-dataset
    """
    # Create a data directory if it doesn't exist
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        logging.info(f"Created directory: {data_dir}")
    
    # Define sample careers data based on the Kaggle dataset structure
    careers_data = [
        {
            "Career_id": 1,
            "Career_title": "Software Developer",
            "Description": "Responsible for designing, coding, and modifying software applications according to client or user requirements. Works with various programming languages and frameworks.",
            "Skills_required": "Programming, Problem-solving, Debugging, Software Design, Version Control, Web Development, Database Management, API Integration",
            "Education_required": "Bachelor's degree in Computer Science or related field",
            "Average_salary": "$105,000",
            "Job_outlook": "22% growth (much faster than average)",
            "Work_environment": "Office-based or Remote",
            "Demand_growth": 0.9
        },
        {
            "Career_id": 2,
            "Career_title": "Data Scientist",
            "Description": "Analyzes and interprets complex data to help organizations make better decisions. Combines expertise in statistics, mathematics, and programming.",
            "Skills_required": "Statistics, Machine Learning, Python, R, SQL, Data Visualization, Big Data Technologies, Problem-solving",
            "Education_required": "Master's or PhD in Statistics, Computer Science, or related field",
            "Average_salary": "$122,000",
            "Job_outlook": "31% growth (much faster than average)",
            "Work_environment": "Office-based or Remote",
            "Demand_growth": 0.95
        },
        {
            "Career_id": 3,
            "Career_title": "UX/UI Designer",
            "Description": "Creates user-friendly interfaces for digital products. Focuses on the look and feel of websites, mobile apps, and software interfaces.",
            "Skills_required": "User Research, Wireframing, Prototyping, Visual Design, User Testing, Adobe Creative Suite, Figma, Sketch",
            "Education_required": "Bachelor's degree in Design, HCI, or related field",
            "Average_salary": "$85,000",
            "Job_outlook": "13% growth (faster than average)",
            "Work_environment": "Office-based or Remote, often in agencies or tech companies",
            "Demand_growth": 0.75
        },
        {
            "Career_id": 4,
            "Career_title": "Digital Marketing Specialist",
            "Description": "Plans and executes marketing campaigns across digital channels to promote products or services and increase brand awareness.",
            "Skills_required": "SEO, SEM, Social Media Marketing, Content Creation, Analytics, Email Marketing, PPC Advertising, Marketing Automation",
            "Education_required": "Bachelor's degree in Marketing, Communications, or related field",
            "Average_salary": "$65,000",
            "Job_outlook": "10% growth (faster than average)",
            "Work_environment": "Office-based or Remote, often in agencies or marketing departments",
            "Demand_growth": 0.7
        },
        {
            "Career_id": 5,
            "Career_title": "Cybersecurity Analyst",
            "Description": "Protects computer systems and networks from cyber threats and responds to security breaches and incidents.",
            "Skills_required": "Network Security, Vulnerability Analysis, Incident Response, Firewall Management, Security Protocols, Ethical Hacking, Cryptography",
            "Education_required": "Bachelor's degree in Cybersecurity, Computer Science, or related field with security certifications",
            "Average_salary": "$99,000",
            "Job_outlook": "33% growth (much faster than average)",
            "Work_environment": "Office-based, sometimes with on-call responsibilities",
            "Demand_growth": 0.92
        },
        {
            "Career_id": 6,
            "Career_title": "Cloud Architect",
            "Description": "Designs and oversees cloud computing strategies and solutions for organizations, ensuring scalability, security, and efficiency.",
            "Skills_required": "Cloud Platforms (AWS, Azure, GCP), Network Architecture, Security, Virtualization, DevOps, Containerization, IaC",
            "Education_required": "Bachelor's degree in Computer Science or related field with cloud certifications",
            "Average_salary": "$128,000",
            "Job_outlook": "15% growth (faster than average)",
            "Work_environment": "Office-based or Remote",
            "Demand_growth": 0.88
        },
        {
            "Career_id": 7,
            "Career_title": "Business Analyst",
            "Description": "Analyzes business needs and processes to recommend improvements and solutions that help organizations achieve their goals.",
            "Skills_required": "Requirements Gathering, Process Modeling, Data Analysis, Project Management, Communication, Documentation, SQL",
            "Education_required": "Bachelor's degree in Business, IT, or related field",
            "Average_salary": "$85,000",
            "Job_outlook": "14% growth (faster than average)",
            "Work_environment": "Office-based or Remote, collaborative team environment",
            "Demand_growth": 0.78
        },
        {
            "Career_id": 8,
            "Career_title": "Product Manager",
            "Description": "Oversees the development and launch of products, from conception to market release, ensuring they meet user needs and business objectives.",
            "Skills_required": "Market Research, Strategic Planning, User Stories, Roadmapping, Agile Methodologies, Cross-functional Collaboration, Analytics",
            "Education_required": "Bachelor's degree in Business, Engineering, or related field",
            "Average_salary": "$110,000",
            "Job_outlook": "8% growth (as fast as average)",
            "Work_environment": "Office-based or Remote, highly collaborative",
            "Demand_growth": 0.82
        },
        {
            "Career_id": 9,
            "Career_title": "DevOps Engineer",
            "Description": "Combines development and operations to improve collaboration and productivity by automating infrastructure, workflows, and continuously measuring application performance.",
            "Skills_required": "CI/CD, Infrastructure as Code, Containerization, Scripting, Cloud Platforms, Monitoring Tools, Version Control, Linux",
            "Education_required": "Bachelor's degree in Computer Science or related field",
            "Average_salary": "$115,000",
            "Job_outlook": "22% growth (much faster than average)",
            "Work_environment": "Office-based or Remote",
            "Demand_growth": 0.9
        },
        {
            "Career_id": 10,
            "Career_title": "AI Engineer",
            "Description": "Develops and implements AI models and systems that can perform tasks requiring human intelligence, such as visual perception, speech recognition, and decision-making.",
            "Skills_required": "Machine Learning, Deep Learning, Python, TensorFlow, PyTorch, Natural Language Processing, Computer Vision, Mathematics",
            "Education_required": "Master's or PhD in Computer Science, AI, or related field",
            "Average_salary": "$135,000",
            "Job_outlook": "31% growth (much faster than average)",
            "Work_environment": "Office-based or Remote, research-oriented environments",
            "Demand_growth": 0.96
        },
        {
            "Career_id": 11,
            "Career_title": "Blockchain Developer",
            "Description": "Develops and implements blockchain-based solutions and systems, including smart contracts and decentralized applications.",
            "Skills_required": "Blockchain Protocols, Smart Contracts, Cryptography, Solidity, Web3.js, Distributed Systems, Security",
            "Education_required": "Bachelor's degree in Computer Science or related field",
            "Average_salary": "$120,000",
            "Job_outlook": "15% growth (faster than average)",
            "Work_environment": "Office-based or Remote, often in startups or financial tech",
            "Demand_growth": 0.85
        },
        {
            "Career_id": 12,
            "Career_title": "Healthcare IT Specialist",
            "Description": "Implements and manages information technology systems within healthcare settings, ensuring data security and compliance with regulations.",
            "Skills_required": "Electronic Health Records, Healthcare Regulations, System Implementation, Technical Support, Data Security, HIPAA Compliance",
            "Education_required": "Bachelor's degree in Health Informatics, IT, or related field",
            "Average_salary": "$88,000",
            "Job_outlook": "9% growth (as fast as average)",
            "Work_environment": "Healthcare facilities, hospitals, clinics",
            "Demand_growth": 0.76
        },
        {
            "Career_id": 13,
            "Career_title": "E-commerce Manager",
            "Description": "Oversees online sales strategies and operations, including website management, customer experience, and digital marketing for online retailers.",
            "Skills_required": "E-commerce Platforms, CRM Systems, Digital Marketing, Analytics, Inventory Management, Customer Experience, Payment Systems",
            "Education_required": "Bachelor's degree in Business, Marketing, or related field",
            "Average_salary": "$78,000",
            "Job_outlook": "10% growth (faster than average)",
            "Work_environment": "Office-based or Remote, retail or e-commerce companies",
            "Demand_growth": 0.79
        },
        {
            "Career_id": 14,
            "Career_title": "Renewable Energy Engineer",
            "Description": "Designs, develops, and implements clean energy solutions such as solar, wind, and hydroelectric power systems.",
            "Skills_required": "Engineering Principles, Renewable Technologies, Project Management, Technical Drawing, Environmental Regulations, Energy Modeling",
            "Education_required": "Bachelor's degree in Engineering with focus on renewable energy",
            "Average_salary": "$92,000",
            "Job_outlook": "8% growth (as fast as average)",
            "Work_environment": "Office and field work, often in remote locations",
            "Demand_growth": 0.84
        },
        {
            "Career_id": 15,
            "Career_title": "Supply Chain Analyst",
            "Description": "Analyzes and optimizes the flow of products and materials from suppliers to consumers, improving efficiency and reducing costs.",
            "Skills_required": "Logistics Management, Data Analysis, Inventory Management, Forecasting, ERP Systems, Process Improvement, Procurement",
            "Education_required": "Bachelor's degree in Supply Chain Management, Business, or related field",
            "Average_salary": "$75,000",
            "Job_outlook": "7% growth (as fast as average)",
            "Work_environment": "Office-based with occasional warehouse or facility visits",
            "Demand_growth": 0.74
        }
    ]
    
    # Define sample market trends data for the careers
    market_trends_data = []
    years = [2020, 2021, 2022, 2023, 2024]
    
    for career in careers_data:
        career_id = career["Career_id"]
        base_demand = career["Demand_growth"] - 0.2  # Starting from a lower point
        
        for i, year in enumerate(years):
            # Gradually increase demand over years
            demand_level = min(1.0, base_demand + (i * 0.05))
            
            # Generate salary trend (percentage change)
            salary_trend = 3 + (i * 0.5) + (career["Demand_growth"] * 2)
            
            # Generate job posting count
            base_postings = int(1000 * career["Demand_growth"])
            job_posting_count = base_postings + (i * int(base_postings * 0.2))
            
            market_trends_data.append({
                "Trend_id": len(market_trends_data) + 1,
                "Career_id": career_id,
                "Year": year,
                "Demand_level": round(demand_level, 2),
                "Salary_trend": round(salary_trend, 2),
                "Job_posting_count": job_posting_count,
                "Source": "Bureau of Labor Statistics",
                "Notes": f"Trend data for {career['Career_title']} in {year}"
            })
    
    # Create DataFrames
    careers_df = pd.DataFrame(careers_data)
    market_trends_df = pd.DataFrame(market_trends_data)
    
    # Save to CSV and JSON files
    careers_csv_path = os.path.join(data_dir, "careers.csv")
    careers_json_path = os.path.join(data_dir, "careers.json")
    market_trends_csv_path = os.path.join(data_dir, "market_trends.csv")
    market_trends_json_path = os.path.join(data_dir, "market_trends.json")
    
    # Save CSV files
    careers_df.to_csv(careers_csv_path, index=False)
    market_trends_df.to_csv(market_trends_csv_path, index=False)
    logging.info(f"Saved career data to CSV: {careers_csv_path}")
    logging.info(f"Saved market trends data to CSV: {market_trends_csv_path}")
    
    # Save JSON files
    with open(careers_json_path, 'w') as f:
        json.dump(careers_data, f, indent=2)
    with open(market_trends_json_path, 'w') as f:
        json.dump(market_trends_data, f, indent=2)
    logging.info(f"Saved career data to JSON: {careers_json_path}")
    logging.info(f"Saved market trends data to JSON: {market_trends_json_path}")
    
    # List all files in the data directory
    files = os.listdir(data_dir)
    logging.info(f"Files in data directory: {files}")
    
    return True

if __name__ == "__main__":
    create_sample_career_dataset()