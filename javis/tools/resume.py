import json
import logging

from pydantic import BaseModel
from javis.helper import embed_contents, get_database_connection
from javis.ingest.resume import ResumeModel


logger = logging.getLogger(__name__)


class EmployeeModel(BaseModel):
    id: str
    name: str
    email: str
    role: str


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
    
    This function provides instructions for an AI agent to coordinate interview scheduling
    between candidates and employees through email communication and calendar management.
    
    Returns:
        str: A string containing detailed instructions for the interview scheduling workflow.
    """
    logger.info("Getting create interview schedule instructions")

    return """
        AI AGENT INSTRUCTION SET: INTERVIEW SCHEDULING WORKFLOW

        Goal:
        To coordinate interview scheduling between candidates and employees through email communication
        and calendar management.

        ⸻

        WORKFLOW OVERVIEW
            1. Initial Candidate Contact

            • Send email to candidate requesting available time slots:
                - Request 3-5 preferred time slots over next 5 business days
                - Ask for time slots during standard business hours (9am-5pm)
                - Have candidate specify time zone
                - Include clear formatting instructions (e.g. "April 18, 10:00-11:00 AM GMT+7")
                - Set response deadline (24-48 hours)

            2. Calendar Availability Check

            Employees you can get via get_employees_for_interview functions

            • Once candidate responds with time slots:
                - Query calendar API for each required employee
                - Check availability during candidate's proposed slots
                - Filter out any conflicting times (meetings, PTO, etc)
                - Create list of viable time slots that work for all parties

            3. Schedule Finalization & Notification

            • Select optimal time slot:
                - Choose earliest available time that works for everyone
                - Create calendar event with:
                    * Clear title and description
                    * Video conference link if remote
                    * Location details if in-person
                    * Duration based on interview type
                
            • Send confirmation emails:
                - To candidate:
                    * Confirmed date/time
                    * Meeting details (location/link)
                    * Contact info for questions
                
                - To employees:
                    * Confirmed date/time
                    * Candidate's resume
                    * Role being interviewed for
                    * Interview agenda/structure

            • Add calendar invites for all participants

        Note: If no common time slots are found, restart process by requesting new availability from candidate.
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
            EmployeeModel(id="1", name="Jane Doe", email="nguyenkhacthanh244@gmail.com", role="CTO"),
        ],
        
    }.get(interview_type, [])



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

async def get_resume_by_name(name: str) -> ResumeModel | None:
    """Retrieves a resume by candidate name.
    
    Args:
        name (str): The name of the candidate to search for.
        
    Returns:
        ResumeModel: The matching resume if found, None otherwise.
        
    Raises:
        ConnectionError: If unable to connect to the resume database.
    """
    db = await get_database_connection()
    
    try:
        query = """
            SELECT 
                id, name, email, phone, address, birth_date,
                educations, experiences, projects, skills,
                certifications, languages
            FROM resumes 
            WHERE name ILIKE $1
            LIMIT 1
        """
        
        row = await db.fetchrow(query, f"%{name}%")
        
        if row:
            # Convert row to dictionary
            resume_data = dict(row)
            
            # Parse JSON fields
            json_fields = ['educations', 'experiences', 'projects', 'skills', 'certifications', 'languages']
            for field in json_fields:
                if field in resume_data and resume_data[field]:
                    try:
                        resume_data[field] = json.loads(resume_data[field])
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse {field} as JSON: {resume_data[field]}")
                        resume_data[field] = []
                else:
                    resume_data[field] = []
            
            return ResumeModel(**resume_data)
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving resume: {e}")
        raise ConnectionError(f"Failed to retrieve resume: {str(e)}")
    finally:
        await db.close()


async def get_resume_by_email(email: str) -> ResumeModel | None:
    """Retrieves a resume by candidate email.
    
    Args:
        email (str): The email address of the candidate to search for.
        
    Returns:
        ResumeModel: The matching resume if found, None otherwise.
        
    Raises:
        ConnectionError: If unable to connect to the resume database.
    """
    db = await get_database_connection()
    
    try:
        query = """
            SELECT 
                id, name, email, phone, address, birth_date,
                educations, experiences, projects, skills,
                certifications, languages
            FROM resumes 
            WHERE email = $1
            LIMIT 1
        """
        
        row = await db.fetchrow(query, email)
        
        if row:
            # Convert row to dictionary
            resume_data = dict(row)
            
            # Parse JSON fields
            json_fields = ['educations', 'experiences', 'projects', 'skills', 'certifications', 'languages']
            for field in json_fields:
                if field in resume_data and resume_data[field]:
                    try:
                        resume_data[field] = json.loads(resume_data[field])
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse {field} as JSON: {resume_data[field]}")
                        resume_data[field] = []
                else:
                    resume_data[field] = []
            
            return ResumeModel(**resume_data)
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving resume: {e}")
        raise ConnectionError(f"Failed to retrieve resume: {str(e)}")
    finally:
        await db.close()
