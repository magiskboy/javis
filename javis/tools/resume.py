import json
import logging

from pydantic import BaseModel
from javis.helper import embed_contents, get_database_connection
from javis.injest.resume import ResumeModel


logger = logging.getLogger(__name__)


class EmployeeModel(BaseModel):
    id: str
    name: str
    email: str
    role: str
    telegram_id: str


class CandidateModel(BaseModel):
    id: str
    name: str
    email: str
    telegram_id: str


async def find_top_match_skills(skills: list[str], k: int = 5) -> list[ResumeModel]:
    """Retrieves resumes that best match the given skills and experience.
    
    This function searches the database for resumes that have the highest
    match rate with the provided skills and experience requirements.
    
    Args:
        skills (list[str]): A list of strings representing required technical skills.
        k (int, optional): The number of top matches to return. Defaults to 5.
        
    Returns:
        list[ResumeModel]: A list of matching resume objects sorted by relevance score.
        
    Raises:
        ConnectionError: If unable to connect to the resume database.
    """
    db = await get_database_connection()

    try:
        # Create embedding for skills query
        skills_content = f"skills: {','.join(skills)}"
        skills_vector = embed_contents([skills_content])[0]
        
        # Build the query based on provided filters
        query = """
            SELECT 
                id, name, email, phone, address, birth_date, 
                educations, experiences, projects, skills, 
                certifications, languages
            FROM resumes ORDER BY vector_skills <=> $1 LIMIT $2
        """

        params = [json.dumps(skills_vector), k]


        logger.info(f"Query: {query}")
        logger.info(f"Params: {params}")

        # Execute the query
        results = await db.fetch(query, *params)
        
        # Process results
        resumes: list[ResumeModel] = []
        for row in results:
            resume = dict(row)
            # Parse JSON fields
            for field in ['educations', 'experiences', 'projects', 'skills', 'certifications', 'languages']:
                if field in resume and resume[field]:
                    resume[field] = json.loads(resume[field])
            resumes.append(ResumeModel(**resume))
        
        return resumes
    
    except Exception as e:
        raise ConnectionError(f"Failed to query resume database: {str(e)}")
    finally:
        await db.close()
    

async def find_top_match_experiences(experience_keywords: list[str], k: int = 5) -> list[ResumeModel]:
    """Find resumes that best match the given experience keywords.
    
    Args:
        experience_keywords: A list of experience keywords to match against.
        k: The maximum number of matching resumes to return.
        
    Returns:
        list[ResumeModel]: A list of matching resume objects sorted by relevance score.
        
    Raises:
        ConnectionError: If unable to connect to the resume database.
    """
    db = await get_database_connection()

    try:
        # Create embedding for experience query
        experience_content = f"experience: {','.join(experience_keywords)}"
        experience_vector = embed_contents([experience_content])[0]
        
        # Build the query based on provided filters
        query = """
            SELECT 
                id, name, email, phone, address, birth_date, 
                educations, experiences, projects, skills, 
                certifications, languages
            FROM resumes ORDER BY vector_experience <=> $1 LIMIT $2
        """

        params = [json.dumps(experience_vector), k]

        logger.info(f"Query: {query}")
        logger.info(f"Params: {params}")

        # Execute the query
        results = await db.fetch(query, *params)
        
        # Process results
        resumes: list[ResumeModel] = []
        for row in results:
            resume = dict(row)
            # Parse JSON fields
            for field in ['educations', 'experiences', 'projects', 'skills', 'certifications', 'languages']:
                if field in resume and resume[field]:
                    resume[field] = json.loads(resume[field])
            resumes.append(ResumeModel(**resume))
        
        return resumes
    
    except Exception as e:
        raise ConnectionError(f"Failed to query resume database: {str(e)}")
    finally:
        await db.close()


def get_create_interview_schedule_instructions() -> str:
    """Returns the instructions for creating an interview schedule.
    
    This function provides a comprehensive set of instructions for an AI agent
    to autonomously coordinate and schedule interviews between job candidates
    and company employees.
    
    Returns:
        str: A string containing detailed instructions for the interview scheduling workflow.
    """
    logger.info("Getting create interview schedule instructions")

    return """
        AI AGENT INSTRUCTION SET: INTERVIEW SCHEDULING WORKFLOW

        Goal:
        To autonomously coordinate and schedule interviews between job candidates and company employees (e.g., CTO, team leader), and notify all involved parties.

        ⸻

        WORKFLOW OVERVIEW
            1.	Candidate Information Collection

            •	Retrieve candidate profile including name, role applied for, contact information, and time zone.
            •	Ask the candidate for a few available time slots in the near future (e.g., next 3–5 days).
            •	Time slots should include date, time range, and time zone (e.g., April 18, 10:00–11:00 AM GMT+7).
            •	Encourage working hour availability unless the candidate specifies otherwise.

            2.	Identify Interview Panel

            •	Determine which employees need to be present in the interview (e.g., CTO, team leader, HR representative).
            •	Retrieve their email addresses or internal identifiers.
            •	Get their roles and link them to the interview stage or type (e.g., technical interview with tech lead).

            3.	Gather Availability of Employees

            •	Check the availability of each selected employee over the next 3–5 working days.
            •	Use calendar APIs or internal systems to find free slots.
            •	Avoid scheduling during existing meetings, breaks, holidays, or out-of-office blocks.
            •	Optionally request confirmation from each employee before finalizing a slot.

            4.	Time Slot Matching

            •	Compare the availability of the candidate with that of the required employees.
            •	Identify the earliest available common time slot that:
        a) Matches everyone’s availability
        b) Respects the candidate’s preferred times
        c) Avoids lunch hours or inconvenient times
            •	Prioritize earlier dates to minimize the waiting period.

            5.	Meeting Creation

            •	Create an interview event in the chosen calendar system.
            •	Select whether the meeting will be online (Zoom, Google Meet, Microsoft Teams) or offline (in-office).
            •	Include title, agenda, time, meeting link or location, and participant list.
            •	Set appropriate duration based on interview type (e.g., 30 minutes for screening, 60 for technical).

            6.	Notification

            •	Send email or calendar invitations to all participants:
        a) To the candidate, including meeting details and contact info for questions
        b) To employees, including the candidate’s resume, job title applied for, and agenda
            •	Provide a method for participants to request rescheduling if needed.

            7.	Logging and Follow-Up

            •	Record the scheduled interview in an internal database or ATS.
            •	Schedule reminder notifications (e.g., 24 hours and 1 hour before the meeting).
            •	In case of changes, reinitiate the availability-checking and rescheduling process.

        ⸻

        OPTIONAL ENHANCEMENTS
            •	Add buffer time before and after interviews for preparation or overruns.
            •	Allow rescheduling by providing a self-service link or automated assistant.
            •	Implement round-robin or load-balancing logic to distribute interviews across available team members.
            •	Support multiple time zone conversions for global teams.
            •	Integrate chatbots for real-time scheduling coordination.

    """


def get_employees_for_interview(interview_type: str) -> list[str]:
    """Get the list of employees required for a specific interview type.
    
    Args:
        interview_type (str): The type of interview to get employees for.
            Supported types include: technical_interview, hr_interview,
            team_lead_interview, product_manager_interview, sales_interview,
            and marketing_interview.
    
    Returns:
        list[str]: A list of employee roles required for the specified interview type.
            Returns an empty list if the interview type is not recognized.
    """
    logger.info(f"Getting employees for interview type: {interview_type}")

    return {
        "technical_interview": [
            EmployeeModel(id="1", name="Jane Doe", email="jane@example.com", role="CTO", telegram_id="1234567890"),
            EmployeeModel(id="2", name="John Smith", email="john@example.com", role="Tech Lead", telegram_id="1234567891")
        ],
        "hr_interview": [
            EmployeeModel(id="3", name="Alice Johnson", email="alice@example.com", role="HR Representative", telegram_id="1234567892")
        ],
        "team_lead_interview": [
            EmployeeModel(id="4", name="Bob Williams", email="bob@example.com", role="Team Leader", telegram_id="1234567893")
        ],
        "product_manager_interview": [
            EmployeeModel(id="5", name="Carol Brown", email="carol@example.com", role="Product Manager", telegram_id="1234567894")
        ],
        "sales_interview": [
            EmployeeModel(id="6", name="David Miller", email="david@example.com", role="Sales Manager", telegram_id="1234567895")
        ],
        "marketing_interview": [
            EmployeeModel(id="7", name="Eva Davis", email="eva@example.com", role="Marketing Manager", telegram_id="1234567896")
        ],
        
    }.get(interview_type, [])


def send_message_via_telegram(message: str, employee: EmployeeModel):
    """Send a message via Telegram to an employee.
    
    Args:
        message (str): The message to send.
        employee (EmployeeModel): The employee to send the message to.

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    logger.info(f"Sending message to {employee.name} via Telegram: {message}")
    return True


def create_interview_schedule(interview_type: str, candidate: CandidateModel, employees: list[EmployeeModel]):
    """Create an interview schedule for a candidate and employees.
    
    Args:
        interview_type (str): The type of interview to create a schedule for.
        candidate (CandidateModel): The candidate to create a schedule for.
        employees (list[EmployeeModel]): The employees to create a schedule for.

    Returns:
        bool: True if the interview schedule was created successfully, False otherwise.
    """
    logger.info(f"Creating interview schedule for {interview_type} with candidate {candidate.name} and employees {employees}")
    return True
