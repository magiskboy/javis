import json
import logging
from javis.helper import embed_contents, get_database_connection
from javis.injest.resume import ResumeModel


logger = logging.getLogger(__name__)


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
