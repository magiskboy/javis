from __future__ import annotations as _annotations
import asyncio
import asyncpg
import json
import logging
import os
from dataclasses import dataclass
from typing import List

from google import genai
from javis import settings
from pydantic import BaseModel
from pydantic_graph import BaseNode, End, Graph, GraphRunContext


class Education(BaseModel):
    period: str
    institution: str
    major: str
    level: str
    notes: str


class Experience(BaseModel):
    period: str
    company: str
    position: str
    notes: str


class Project(BaseModel):
    name: str
    company: str
    description: str
    members: int
    position: str
    technologies: List[str]


class Skill(BaseModel):
    name: str
    level: str


class Certification(BaseModel):
    name: str
    organization: str


class Language(BaseModel):
    name: str
    level: str 


class ResumeModel(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    birth_date: str
    educations: List[Education]
    experiences: List[Experience]
    projects: List[Project]
    skills: List[Skill]
    certifications: List[Certification]
    languages: List[Language]


@dataclass
class State:
    uploaded_file: genai.types.File
    parsed_data: ResumeModel
    vectorized_data: tuple[list[float], list[float]]


@dataclass
class Deps:
    logger: logging.Logger
    db: asyncpg.Connection
    client: genai.Client


@dataclass
class Start(BaseNode[State, Deps, str]):
    filename: str

    async def run(self, ctx: GraphRunContext[State, Deps]) -> "Upload":
        db = ctx.deps.db
        await db.execute('''
        CREATE EXTENSION IF NOT EXISTS vector;
        ''')

        await db.execute(f'''
            CREATE TABLE IF NOT EXISTS resumes (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(255),
                address VARCHAR(255),
                birth_date VARCHAR(255),
                educations JSONB,
                experiences JSONB,
                projects JSONB,
                skills JSONB,
                certifications JSONB,
                languages JSONB,
                vector_skills vector({settings.VECTOR_DIMENSION}) NOT NULL,
                vector_experience vector({settings.VECTOR_DIMENSION}) NOT NULL
            )
        ''')
        return Upload(filename=self.filename)


@dataclass
class Upload(BaseNode[State, Deps]):
    filename: str

    async def run(self, ctx: GraphRunContext[State, Deps]) -> "Parse":
        client = ctx.deps.client
        file = client.files.upload(
            file=self.filename,
            config=dict(
                mime_type="application/pdf",
            )
        )
        ctx.state.uploaded_file = file
        return Parse()


@dataclass
class Parse(BaseNode[State, Deps]):
    async def run(self, ctx: GraphRunContext[State, Deps]) -> "Embed":
        model = settings.GEMINI_MODEL
        client = ctx.deps.client
        response = client.models.generate_content(
            model=model,
            contents=[ctx.state.uploaded_file],
            config=dict(
                response_mime_type="application/json",
                response_schema=ResumeModel
            )
        )
        ctx.state.parsed_data = ResumeModel.model_validate_json(response.text)
        return Embed()
    

@dataclass
class Embed(BaseNode[State, Deps]):
    async def run(self, ctx: GraphRunContext[State, Deps]) -> "Store":
        resume = ctx.state.parsed_data

        skills_content = f"skills: {','.join([f'{skill.name}:{skill.level}' for skill in resume.skills])}"
        experience_content = f"experience: {','.join([experience.position for experience in resume.experiences])}"

        client = ctx.deps.client
        response = client.models.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            contents=[
                skills_content,
                experience_content,
            ],
        )

        ctx.state.vectorized_data = (response.embeddings[0].values, response.embeddings[1].values)
        return Store()
    

class Store(BaseNode[State, Deps]):
    async def run(self, ctx: GraphRunContext[State, Deps]) -> End:
        logger = ctx.deps.logger
        logger.info(f"Storing resume: {ctx.state.parsed_data}")
        db = ctx.deps.db

        resume = ctx.state.parsed_data
        resume_data = resume.model_dump()

        await db.execute("""
            INSERT INTO resumes (
                name, email, phone, address, birth_date, educations, experiences, projects, skills, certifications, languages, vector_skills, vector_experience
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
            )
        """,
            resume.name,
            resume.email,
            resume.phone,
            resume.address,
            resume.birth_date,
            json.dumps(resume_data['educations']),
            json.dumps(resume_data['experiences']),
            json.dumps(resume_data['projects']),
            json.dumps(resume_data['skills']),
            json.dumps(resume_data['certifications']),
            json.dumps(resume_data['languages']),
            json.dumps(ctx.state.vectorized_data[0]),
            json.dumps(ctx.state.vectorized_data[1]),
        )
        return End(data=None)


async def main():
    resume_folder = os.path.join(settings.DATA_DIR, "resume")

    # Initialize dependencies
    db = await asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME
    )
    logger = logging.getLogger(__file__)
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    deps = Deps(
        logger=logger,
        db=db,
        client=client
    )

    # Initialize state
    state = State(
        uploaded_file=None,
        parsed_data=None,
        vectorized_data=None
    )

    # Construct the graph
    graph = Graph(nodes=[
        Start,
        Upload,
        Parse,
        Embed,
        Store,
    ])


    filename = os.path.join(resume_folder, 'Đỗ Trọng Hiếu.pdf')
    await graph.run(Start(filename), deps=deps, state=state)


if __name__ == "__main__":
    asyncio.run(main())