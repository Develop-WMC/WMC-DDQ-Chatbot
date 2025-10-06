import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime
import os

# ============================================================================
# PAGE CONFIG - Must be first Streamlit command
# ============================================================================

st.set_page_config(
    page_title="WMC DDQ Portal",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CUSTOM CSS - Production Level
# ============================================================================

def load_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Custom header */
    .custom-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
        color: white;
    }
    
    .company-name {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .company-tagline {
        font-size: 1.1rem;
        font-weight: 300;
        opacity: 0.9;
    }
    
    /* Login form styling */
    .login-container {
        max-width: 400px;
        margin: 4rem auto;
        padding: 3rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    }
    
    .login-title {
        text-align: center;
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 2rem;
        color: #333;
    }
    
    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        max-width: 900px;
        margin: 0 auto;
    }
    
    /* Chat messages */
    .stChatMessage {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Input fields */
    .stTextInput input {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
        font-size: 1rem;
    }
    
    .stTextInput input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Metrics */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Info boxes */
    .info-box {
        background: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #e8f5e9;
        border-left: 4px solid #4CAF50;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Contact card */
    .contact-card {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .contact-name {
        font-weight: 600;
        font-size: 1.1rem;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    .contact-info {
        color: #666;
        margin: 0.3rem 0;
    }
    
    /* Chat input */
    .stChatInputContainer {
        border-top: 2px solid #e0e0e0;
        padding-top: 1rem;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #f8f9fa;
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Get API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", st.secrets.get("GEMINI_API_KEY", ""))

# Model configuration
MODEL_NAME = "gemini-2.0-flash-exp"

# Safety settings
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Generation config
GENERATION_CONFIG = {
    "temperature": 0.1,
    "top_p": 0.8,
    "top_k": 20,
    "max_output_tokens": 4096,
}

# Initialize the model
@st.cache_resource
def initialize_model():
    """Initialize Gemini model with caching for better performance"""
    try:
        if not GEMINI_API_KEY:
            st.error("⚠️ GEMINI_API_KEY not found. Please set it in your environment or secrets.")
            return None
            
        genai.configure(api_key=GEMINI_API_KEY)
        
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=GENERATION_CONFIG,
            safety_settings=SAFETY_SETTINGS
        )
        return model
    except Exception as e:
        st.error(f"❌ Failed to initialize model: {e}")
        return None

# User credentials - CHANGE THESE FOR PRODUCTION
USERS = {
    "jpmorgan": "JPM_secure_2025",
    "hsbc": "HSBC_pass_456",
    "goldman": "GS_secure_789",
    "demo": "demo123",
    "admin": "Admin_WMC_999"
}

# ============================================================================
# KNOWLEDGE BASE - Full Content from Your Documents
# ============================================================================

KNOWLEDGE_BASE = """
# WMC Due Diligence Knowledge Base - Complete Information

## DOCUMENT 1: Frequently Asked Questions - Due Diligence on WMC
Last update: 22nd September 2025

### Internal Controls & Audit

**Question: Does your Company have any legal, regulatory or internal control procedures to ensure confidentiality of information about clients, handle conflicts of interests with clients, or implement the code of ethics?**
Answer: Yes, we have legal, regulatory or internal control procedures to ensure confidentiality of information about clients, handle conflicts of interests with clients, and implement the code of ethics.

**Question: Does your Company have an internal audit function or other independent third party that assesses your internal control policies and practices on a regular basis?**
Answer: We do not have internal audit. But we have external audit to review our policies and practices. The frequency of review is annually. The last review was conducted in April 2024.

**Question: Any material finding in the last external audit?**
Answer: No

**Question: Who is the Auditor?**
Answer: D & Partners CPA Limited

### Sub-Distributors & Complaints

**Question: Why sub-distributors are not required to make WMC aware of any investor complaints?**
Answer: Our sub-distributors are SFC licensed corporations. We regularly monitor the enforcement announcements on the SFC website to see if there are any matching cases. They are under regulatory oversight with annual audits. If we see there is an enforcement cases related to the sub distributor or their employees, we would request them to address our concern and see if there is any internal control enhancement to fix the deficiency in the compliant standard.

**Question: Are sub-distributors required to make you aware of any relevant complaints?**
Answer: Our sub-distributors are SFC licensed corporations. We regularly monitor the enforcement announcements on the SFC website to see if there are any matching cases. They are under regulatory oversight with annual audits. If we see there is an enforcement cases related to the sub distributor or their employees, we would request them to address our concern and see if there is any internal control enhancement to fix the deficiency in the compliant standard.

### Source of Funds & Clients

**Question: Source of funds for UBO**
Answer: Clients' money

**Question: Source of Wealth for UBO**
Answer: Clients' money

**Question: What is the Country(s) of origin of your Source of Funds?**
Answer: Mainly from Hong Kong. WMC has clients from SFC licensed Corporation and individual investors reside in Hong Kong. WMC still have small number of clients has Singapore, Australia, United Kingdom bank accounts to deposit money to WMC.

Those individuals can provide Hong Kong ID card to prove they are resident in Hong Kong. Some non-Hong Kong address included China, Australia, Singapore, Malaysia, United Kingdom.

Mainly in Hong Kong, China as most of the corporate account are SFC licensed corp. Authorized signatories are staffs in the SFC licensed corporation.

**Question: Does WMC have a significant (10% or more) non-resident client base, either by number of clients or by revenues?**
Answer: No. The number of clients from a non-Hong Kong resident base is less than 10%.

**Question: Country of domicile of underlying customers (top 5)**
Answer: 
1. Australia
2. China
3. Isle of Man
4. Singapore
5. Malaysia

**Question: Are any of the sub-distributors located in High Risk jurisdictions?**
Answer: No.

### Management Changes

**Question: Please advise whether there has been any major change in senior management over the past 3 years? If yes, please briefly provide the name and the year of change.**
Answer: Ng Sai Tong becomes the executive director of Wealth Management Cube Limited in 2022.

### WMC Nominee Limited

**Question: What is the function of the entity WMC Nominee Limited?**
Answer: WMC Nominee Limited is not a trust or company service provider under TCSP. The only function of WMC Nominee Limited is to hold the client assets and separate the client assets from Wealth Management Cube Limited. Therefore, it is registered under SFC and have a CE number and own SFC portal login.

**Question: What is an associated entity?**
Answer: Please see the answer on SFC's website and relevant legislation in below links:
https://www.sfc.hk/en/faqs/intermediaries/licensing/Associated-entities
Cap. 571 Securities and Futures Ordinance (elegislation.gov.hk)

### Information Technology

**Question: Is your firm, in all material aspects, complying with the MAS Technology Risk Management Guidelines? If not, please state if you are in compliance with other technology guidelines or standards?**
Answer: No. Our company strictly adheres to the Hong Kong SFC's requirements for External Electronic Data Storage Providers (EDSP), specifically:

1. Regulatory Compliance & Data Management
- Maintain full set of regulatory records accessible from Hong Kong office without undue delay
- Implement comprehensive audit trails for all data access and modifications
- Ensure proper data backup and recovery procedures with daily backups
- Maintain detailed Access Map of regulatory record locations

2. AWS Cloud Platform Implementation
- Utilize AWS's globally distributed infrastructure with multiple availability zones
- Leverage AWS security certifications (SOC 1/2/3, ISO 27001/27017/27018)
- Implement AWS monitoring tools (CloudTrail, CloudWatch) for audit requirements
- Maintain business continuity through AWS's redundant infrastructure

3. Internal Controls & Policies
- Documented policies for data access, storage, and retrieval
- Strict user access management and authentication controls
- Regular testing of business continuity procedures
- Ongoing monitoring and incident response protocols

4. Security & Risk Management
- Comprehensive information security measures
- Regular due diligence on AWS as our EDSP
- Documented disaster recovery procedures
- Continuous compliance monitoring and reporting

All implementations align with SFC circular requirements (19EC59) and associated FAQs regarding external electronic data storage.

**Question: Has there been material changes to your IT infrastructure (including use of dedicated hardware i.e. servers/network devices) or cloud services? Has there been material changes to your system architecture involving multi-tenancy and data commingling for the services provided?**
Answer: No material changes to IT infrastructure. No material changes to system architecture involving multi-tenancy.

**Question: If the services are provided using a cloud-based solution, please indicate the cloud provider and provide an illustration of your cloud solution.**
Answer: We use AWS (Amazon Web Services) as our cloud service provider.

Architecture Overview:
- VPC (Virtual Private Cloud) with public and private subnets for security isolation
- Components include:
  * Web Components in public subnet
  * Database (SQL Server) in private subnet
  * AWS Lambda for serverless computing
  * Load balancer (LB) for traffic management
  * Security groups and network ACLs for access control

Security Assessments:
- AWS provides various compliance reports and certifications through AWS Artifact, including SOC 1, 2, and 3 reports, ISO 27001, 27017, and 27018 certifications, and PCI DSS compliance reports
- Our architecture implements AWS security best practices including network isolation using VPC, private subnets for sensitive data, encryption at rest and in transit, access control through security groups, and regular monitoring and alerting
- No material findings have been identified in security assessments

Control Procedures:
Our system architecture ensures:
1. Data Isolation: Customer data is stored in dedicated SQL Server database, private subnet deployment for database access, network segmentation through VPC design
2. Data Confidentiality: Secure access through load balancer, encrypted data transmission, role-based access control

There have been no material changes to these control procedures.

**Question: Please state and provide all available certificate/security/features around your IT infrastructure.**
Answer: Our IT infrastructure leverages AWS cloud services with comprehensive security features implemented:

1. Network Security: Virtual Private Cloud (VPC) with public and private subnet segregation, Security Groups and Network ACLs for strict access control, Controlled routing configurations for network traffic management

2. Identity and Access Management: IAM (Identity and Access Management) implementation, Multi-factor Authentication (MFA), Strict password policies, Role-based access control

3. Encryption and Data Protection: AWS KMS (Key Management Service) for encryption key management, S3 bucket encryption for secure storage, Data encryption policies

4. Monitoring and Logging: CloudWatch monitoring and alerts, CloudTrail for API activity logging and audit trails, Comprehensive logging and monitoring metrics

5. Infrastructure Security: AWS provided physical and environmental security, Regular security patches and updates, Secure access points and protocols

While we leverage AWS's secure infrastructure, we maintain our own security controls and regularly review our security posture to ensure alignment with industry best practices.

**Question: Does your firm have procedures to securely destroy or remove the firm's customer information when the need arises?**
Answer: Our firm has established procedures for secure data destruction and removal of customer information when required. These procedures are implemented through our AWS infrastructure:

1. Database Level Deletion: Secure deletion procedures in SQL Server database

2. Storage Level Removal: Secure deletion of data in AWS S3 storage, Implementation of object lifecycle policies, Versioning control for data management

3. Security Measures: Access controls to prevent unauthorized deletion, Audit logging of all deletion activities through CloudTrail, Regular monitoring of deletion processes through CloudWatch

There have been no material changes to these procedures.

**Question: Has there been material changes to the firm's policy around storage of sensitive data? Please indicate where the sensitive data is stored including any offshore locations.**
Answer: No material changes have been made to our firm's sensitive data storage policy. Our policies continue to align with AWS best practices and regulatory requirements.

All sensitive data is stored within AWS infrastructure in the Asia Pacific (Hong Kong) region. Specifically:
- Customer data is stored in SQL Server databases within private VPC subnets
- File storage is managed through AWS S3 with encryption enabled
- No offshore storage locations are used for sensitive data

**Question: Has there been a Threat and Vulnerability Risk Assessment performed on the physical security and environmental controls of the data centre over the trailing 12 months?**
Answer: As we utilize AWS infrastructure, our data center physical security and environmental controls benefit from AWS's comprehensive security assessments. AWS manages the physical security of the data centers. AWS maintains SOC reports covering physical and environmental controls.

For our specific implementation, we conduct regular security reviews of our network configurations, access controls, security group settings, and encryption implementations.

**Question: Do you employ multi-factor authentication (MFA) for sensitive systems?**
Answer: Yes, we employ multi-factor authentication for sensitive systems:
- MFA is enabled for AWS Console access
- MFA is required for all administrative access
- Additional authentication factors include time-based one-time passwords (TOTP) and hardware security keys where applicable

**Question: Please indicate if there are material changes in the performance of the below controls:**
Answer: There are no material changes in the performance of these controls. Our current implementation includes:

(a) Privileged Account Monitoring: All privileged account activities are logged through AWS CloudTrail, Regular reviews of IAM user activities, Automated alerts for suspicious privileged account activities, Monitoring through CloudWatch

(b) Log Protection: AWS CloudTrail logs are stored in dedicated S3 buckets with encryption, Log files are protected with strict access controls, Immutable logging enabled to prevent tampering, Version control enabled for audit trails

(c) Access Restrictions: Strict IAM policies implementing principle of least privilege, Security groups controlling access to services, Private subnets for sensitive services, Role-based access control implementation

(d) Integrity Checks: AWS Config rules for configuration monitoring, Database integrity monitoring, Regular system configuration audits, Automated alerts for unauthorized changes

(e) Password Controls Review: Regular password policy compliance checks, Enforcement of strong password requirements through IAM, Periodic password rotation requirements, Regular review of password policies

(f) Access Rights Review: Regular IAM user access reviews, Periodic audit of security group permissions, Regular review of role assignments, Automated inactive account detection

No lapses have been identified in relation to services rendered in any of these areas. Our monitoring systems have not detected any security incidents or compliance violations.

### Compliance Monitoring Program

**Question: Please confirm that the Company has established, implemented and maintain a compliance monitoring program, i.e. how does it ensure that your Compliance manual is followed by all of its employees.**
Answer: All employees are required to attend Compliance Training Sessions held by Management to ensure that they understand the legal and compliance issues involved related to their positions, and the standards and practices expected of them by the Company and the Hong Kong Securities and Futures Commission. All staffs are tested on the materials of the Compliance Manual to ensure competence. Controls are set up to govern all essential procedures with strict observation of compliance requirements, and all Management are required to ensure the established control and policies are executed with prudence by all staffs.

### Cybersecurity

**Question: Has cybersecurity training been provided to staff? What is the frequency of such training? When was the last training held and what did it cover?**
Answer: Cybersecurity training has been provided to staff on an annual basis, with the most recent session held on NOV, 2023 through a video training format. The yearly training covers comprehensive cybersecurity topics including common cyber threats (phishing scams, malware, ransomware, social engineering, and data breaches) as well as practical security measures such as email security, safe internet browsing, and mobile device security, ensuring staff maintain up-to-date knowledge of cybersecurity best practices and awareness of current threats.

**Question: Do you have a cybersecurity policy? Is there a designated cyber security officer? Has the policy been reviewed by an external consultant? Is the policy followed by any other third parties?**
Answer: WMC has a formal cybersecurity policy documented in the WMC IT Policy. While there isn't a specifically designated cybersecurity officer, IT security responsibilities are managed through the Administrator and company policy compliance officer roles as defined in the policy. The policy underwent regulatory review during a recent SFC visit. Regarding third parties, the policy mandates that any external connections to company IT facilities must comply with the Company's IT Security and Privacy Policy, though specific third-party agreements would need to be verified separately.

**Question: Describe how cybersecurity is managed, including a description of the controls in place (namely, anti-virus software, vulnerability and intrusion testing) and the frequency at which vulnerability scanning is conducted, and updates/patches applied to all systems.**
Answer: Cybersecurity is managed through a layered control system that includes firewall implementation for monitoring all incoming and outgoing Internet traffic, with all network traffic being scanned and filtered by anti-virus software. System protection measures include mandatory virus scanning, particularly for external media and notebooks reconnecting to the network after external use. Users are required to perform regular PC maintenance including Scandisk and virus scans on a quarterly basis. Access controls are maintained through password protection policies, file-level security, and data encryption for confidential information.

**Question: Have you experienced any cybersecurity breaches or incidents? If so, how were they handled?**
Answer: No.

### Business Continuity Plan (BCP)

**Question: For BCP, how often is this performed, e.g. annually? When was it last performed and are there any findings?**
Answer: Annually. The last BCP was performed on 19th November 2024. There are no material findings in the review.

### Ownership Structure

**Question: Could the prospect elaborate the rationale for such ownership structure, including the three separate holding lines as well as the utilization of three different holding companies?**
Answer: Rationale for such ownership structure is for tax optimization.

**Question: Do these holding companies hold any other operating companies?**
Answer: The three holding companies, namely Wellchamp Investments Limited, Wellchamp Fund Limited and Wellchamp Capital Limited, do not hold any operating company.

### Record Keeping

**Question: Do you have the ability to maintain books and records on behalf of Sofi Invest in compliance with Exchange Act Rules 17a-3 and 17a-4, as well as FINRA Rule 3110(b)(4) and FINRA Rule Series 4510 or other applicable laws, rules and regulations?**
Answer: Hong Kong's SFC recordkeeping rules under the SFO, Keeping of Records Rules, and Code of Conduct serve a similar purpose to the U.S. rules -- ensuring licensed corporations keep accurate, accessible, and supervisory‑compliant books and records.

---

## DOCUMENT 2: Due Diligence of WMC (Version 202401, amended 20241219)

### Basic Information

**Legal Name of the Company:** Wealth Management Cube Limited (WMC)

**Address:** 804A2, 8/F, World Wide House, 19 Des Voeux Road Central, Central, Hong Kong

**Company Registration No.:** CI No.: 2116198

**Date of incorporation:** 04 JULY 2014

**Company ownership chart:** Will provide upon request (including ultimate beneficial owners more than 20% of the shares and their respective percentage of shares held)

**Company's insurance coverage:**
- Type of insurance: Professional Indemnity
- Insurance company: Chubb Elite Financial Institutions Civil Liability Insurance
- Amount insured: HKD 7,500,000

**Compliance Officer Contact Details:**
- Name: Lau Hiu Fung Peter
- Tel: 852 3854 6419
- Email: peterlau@wmcubehk.com

**Brief background profile:**
WMC is a SFC licensed corporation (CE No. BEC913) in Hong Kong Established in 2014. We are providing B2B & B2B2C Fund Investment Dealing & Settlement services and Insurance Admin & CRM solutions. Our principal activity of the Company is the provision of platform servicing for financial institutions. Our clients are mainly Financial Advisory firms (FAs) which make use of our platform in the dealing of investment products for their end-investors. We have around 18 staffs now.

### SFC Associated Entity Information

**Question: What is an associated entity under SFC regulations?**
Answer: Under Section 165(3) of the Securities and Futures Ordinance, an associated entity of an intermediary (other than an authorized financial institution) cannot conduct any business other than receiving or holding client assets, whether on behalf of an intermediary or otherwise, unless authorized in writing by the SFC.

**Question: If an associated entity is also a licensed corporation, does it require written authorization from the SFC?**
Answer: If the licensed corporation notifies the SFC that it has become an associated entity of another intermediary, there is no need to seek additional authorization under Section 165(3). It may continue to carry out its regulated activity(ies) as a licensed corporation.

**Question: Can entities in the same group make a single notification for changes?**
Answer: Yes. For entities belonging to the same group of companies, a licensed corporation (or registered institution) may make a notification required under the Associated Entities - Notice Rules on its behalf and on behalf of other group entities in respect of the same change in information. The notification should clearly state on whose behalf it is made, and the represented entities should be aware of the notification.

**Question: Can a licensed corporation that is also an associated entity make a single notification under both rules?**
Answer: Yes. Where the licensed corporation (or registered institution) is also an associated entity, a single notification for the same change in information is acceptable provided that the capacities under which the notification is made is clearly stated.

**Question: Can a licensed corporation that is also an associated entity make a single submission of financial statements?**
Answer: Yes. A single submission by a licensed corporation that is also an associated entity is acceptable provided that the submission complies with the requirements under the Accounts and Audit Rules for a licensed corporation and states the capacities of the corporation.
"""

# ============================================================================
# SESSION STATE
# ============================================================================

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

# ============================================================================
# FUNCTIONS
# ============================================================================

def save_conversation_log(username, question, answer):
    """Save conversation to log file"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "question": question,
        "answer": answer
    }
    
    try:
        with open("conversation_logs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        # Silently fail if logging doesn't work
        pass

def get_gemini_response(question):
    """
    Get response from Gemini API with STRICT anti-hallucination measures
    """
    try:
        # Get the cached model
        model = initialize_model()
        if not model:
            return "Error: Model initialization failed. Please check your API key."
        
        # STRICT PROMPT to prevent hallucination
        prompt = f"""You are a Due Diligence Assistant for Wealth Management Cube Limited (WMC), a Hong Kong SFC-licensed fund platform.

【CRITICAL RULES - YOU MUST FOLLOW STRICTLY】

1. ❌ You can ONLY use information from the KNOWLEDGE BASE below
2. ❌ You CANNOT make up, guess, assume, or use any external knowledge
3. ❌ If the information is NOT in the KNOWLEDGE BASE, you MUST say exactly: "I don't have that specific information in our DDQ documents. Please contact our Compliance Officer, Peter Lau, at peterlau@wmcubehk.com or +852 3854 6419 for more details."
4. ✅ Be professional, concise, and accurate
5. ✅ Include relevant details (dates, numbers, names) when available in the documents
6. ✅ Quote directly from the documents when possible
7. ❌ Never say things like "based on industry standards" or "typically" or "probably" - only use what's in the documents

【KNOWLEDGE BASE - START】
{KNOWLEDGE_BASE}
【KNOWLEDGE BASE - END】

【USER QUESTION】
{question}

【YOUR ANSWER】
(Answer based ONLY on the KNOWLEDGE BASE above. If the information is not found, use the "I don't have that information" template provided in rule 3.)
"""
        
        # Generate response with proper error handling
        response = model.generate_content(prompt)
        
        # Check if response was blocked
        if not response or not response.parts:
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                block_reason = getattr(response.prompt_feedback, 'block_reason', 'Unknown reason')
                return f"⚠️ Response was blocked: {block_reason}. Please rephrase your question."
            return "⚠️ No response generated. Please try again or contact Peter Lau at peterlau@wmcubehk.com or +852 3854 6419."
        
        # Extract text from response
        answer = response.text if hasattr(response, 'text') else str(response)
        return answer
        
    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            return "⏱️ Request timed out. Please try again or contact Peter Lau at peterlau@wmcubehk.com or +852 3854 6419."
        elif "API key" in error_msg or "api_key" in error_msg.lower():
            return "❌ API key error. Please check your Gemini API configuration."
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            return "❌ API quota exceeded. Please try again later or contact support."
        return f"❌ Error: {error_msg}\n\nPlease contact our Compliance Officer, Peter Lau, at peterlau@wmcubehk.com or +852 3854 6419."

# ============================================================================
# UI PAGES
# ============================================================================

def login_page():
    """Professional login page"""
    load_css()
    
    # Header
    st.markdown("""
        <div class="custom-header">
            <div class="company-name">🏢 Wealth Management Cube</div>
            <div class="company-tagline">Due Diligence Information Portal</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">🔐 Secure Login</div>', unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username", placeholder="Enter your username", key="login_user")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submit = st.form_submit_button("🔓 Login", use_container_width=True)
            with col_btn2:
                st.form_submit_button("❌ Clear", use_container_width=True)
            
            if submit:
                if username in USERS and USERS[username] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("✅ Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Info box
        with st.expander("ℹ️ Demo Access"):
            st.markdown("""
                <div class="info-box">
                    <strong>Demo Credentials:</strong><br>
                    Username: <code>demo</code><br>
                    Password: <code>demo123</code>
                </div>
            """, unsafe_allow_html=True)
        
        # Footer
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.caption("🔒 Secure connection • All conversations are logged for compliance")
        st.caption(f"🤖 Powered by {MODEL_NAME}")

def chat_page():
    """Professional chat interface"""
    load_css()
    
    # Custom header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("""
            <div class="custom-header">
                <div class="company-name">💬 DDQ Assistant</div>
                <div class="company-tagline">Ask me anything about WMC's Due Diligence</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.write("")
        st.write("")
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.messages = []
            st.rerun()
    
    # User info badge
    st.markdown(f"""
        <div class="success-box">
            🟢 Logged in as: <strong>{st.session_state.username}</strong>
        </div>
    """, unsafe_allow_html=True)
    
    # Main chat area
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Welcome message
    if len(st.session_state.messages) == 0:
        st.session_state.messages.append({
            "role": "assistant",
            "content": """👋 **Welcome to the WMC Due Diligence Portal!**

I can help you with questions about:
- 🏢 Company information & registration
- ✅ Compliance procedures & audits  
- 🔒 IT infrastructure & cybersecurity
- 👤 AML/KYC processes
- 📋 Business continuity plans
- 🏗️ Ownership structure
- 💼 Professional indemnity insurance
- 📊 Staff information & management

**Please ask me anything about WMC's due diligence information.**

*Note: I only provide information from our official DDQ documents. If you need additional details not covered in the documents, I'll direct you to our Compliance Officer.*"""
        })
    
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("💭 Type your question here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔍 Searching our DDQ documents..."):
                response = get_gemini_response(prompt)
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_conversation_log(st.session_state.username, prompt, response)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Session Info")
        
        questions_asked = len([m for m in st.session_state.messages if m["role"] == "user"])
        
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{questions_asked}</div>
                <div class="metric-label">Questions Asked</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("### 🏢 Company Info")
        st.markdown("""
            <div class="contact-card">
                <strong>Wealth Management Cube Ltd</strong><br>
                📍 804A2, 8/F, World Wide House<br>
                19 Des Voeux Road Central<br>
                Central, Hong Kong<br><br>
                🏢 SFC License: CE No. BEC913<br>
                📅 Established: 2014<br>
                👥 Staff: 18-20 people
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("### 📞 Contact")
        st.markdown("""
            <div class="contact-card">
                <div class="contact-name">Lau Hiu Fung Peter</div>
                <div style="color: #888; font-size: 0.9rem;">Compliance Officer</div>
                <div class="contact-info">📧 peterlau@wmcubehk.com</div>
                <div class="contact-info">📱 +852 3854 6419</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("### ℹ️ About This Tool")
        st.info(f"""
This AI assistant provides information from WMC's official Due Diligence documents only. 

It will **not** make up information. If something is not in our documents, it will tell you to contact our Compliance Officer.

🤖 Model: {MODEL_NAME}
🌡️ Temperature: {GENERATION_CONFIG['temperature']}
        """)
        
        # Admin tools
        if st.session_state.username == "admin":
            st.markdown("---")
            st.markdown("### 🔧 Admin Tools")
            
            if st.button("📥 Download Conversation Logs", use_container_width=True):
                try:
                    with open("conversation_logs.jsonl", "r", encoding="utf-8") as f:
                        logs = f.read()
                    st.download_button(
                        "⬇️ Download Logs (JSONL)",
                        logs,
                        "conversation_logs.jsonl",
                        "application/json",
                        use_container_width=True
                    )
                except FileNotFoundError:
                    st.warning("No logs available yet")
                except Exception as e:
                    st.error(f"Error: {e}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        chat_page()

if __name__ == "__main__":
    main()

