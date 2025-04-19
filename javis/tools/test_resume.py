import unittest
import asyncio
import json

from javis.tools import resume
from javis.injest.resume import (
    ResumeModel,
    Education,
    Experience,
    Project,
    Skill,
    Certification,
    Language,
)
from javis import settings
from javis.helper import get_database_connection


class TestResume(unittest.TestCase):
    async def async_tearDown(self):
        if hasattr(self, "conn"):
            # Drop test table
            await self.conn.execute("DROP TABLE IF EXISTS resumes")
            # Close connection
            await self.conn.close()

    def test_find_top_match_skills(self):
        async def run_test():
            try:
                # Test finding matches by skills
                skills = ["Python", "Machine Learning"]
                results = await resume.find_top_match_skills(skills, k=5)
                self.assertEqual(len(results), 5)
                print(f"results: {results}")
            finally:
                # Cleanup
                await self.async_tearDown()

        asyncio.run(run_test())

    def test_find_top_match_experiences(self):
        async def run_test():
            try:
                # Test finding matches by experience
                experience_keywords = ["Software Engineer", "Developer"]
                results = await resume.find_top_match_experiences(
                    experience_keywords, k=5
                )

                self.assertEqual(len(results), 5)
                print(f"results: {results}")
            finally:
                # Cleanup
                await self.async_tearDown()

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
