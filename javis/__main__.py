import asyncio
from dataclasses import dataclass
import json

from javis import settings
from javis.agent import create_agent
from javis.helper import embed_contents, get_database_connection
from javis.telegram_bot import TelegramBot
from javis.agent import create_agent, process_prompt
import click
from javis import settings
from javis.migrations import run_migrations


@dataclass
class Message:
    session_id: str
    user_id: str
    content: str
    date: str


cli = click.Group()


@cli.command()
def run_local():
    async def run():
        agent = create_agent()

        while True:
            try:
                user_input = input("> ")

                content = await process_prompt(user_input, agent, "1")
                print("javis:", content)

            except KeyboardInterrupt:
                break

    asyncio.run(run())


@cli.command()
def run_bot():
    telegram_bot = TelegramBot(settings.TELEGRAM_BOT_TOKEN)
    telegram_bot.run()


@cli.command()
<<<<<<< HEAD
def run_email_task():
    from javis.tools.email_monitor_task import start_monitoring

    async def _inner():
        await asyncio.gather(
            start_monitoring(),
        )

    asyncio.run(_inner())


@cli.command()
def re_calculate_vectors():
    async def re_calculate_vector_skills():
        """Re-calculate the vector skills for all resumes.

=======
def re_calculate_vectors():
    async def re_calculate_vector_skills():
        """Re-calculate the vector skills for all resumes.
        
>>>>>>> 386f40c1562c (wip)
        This function re-calculates the vector skills for all resumes in the database.
        It uses the embed_contents function to calculate the vector skills for each resume.
        """
        click.echo("Re-calculating vector skills for all resumes")

        db = await get_database_connection()
        try:
            query = """
                SELECT id, skills, experiences FROM resumes
            """
            results = await db.fetch(query)

            click.echo(f"Records: {[r['id'] for r in results]}")
<<<<<<< HEAD

            for r in results:
                skills_content = ",".join(
                    [
                        f'{skill["name"]}:{skill["level"]}'
                        for skill in json.loads(r["skills"])
                    ]
                )
                skills_content = f"skills: {skills_content}"
                experience_content = ",".join(
                    [
                        f'{experience["company"]}:{experience["position"]}'
                        for experience in json.loads(r["experiences"])
                    ]
                )
                experience_content = f"experience: {experience_content}"

                [skills_vector, experience_vector] = embed_contents(
                    [(skills_content), experience_content]
                )

                await db.execute(
                    """
                    UPDATE resumes SET vector_skills = $1, vector_experience = $2 WHERE id = $3
                """,
                    json.dumps(skills_vector),
                    json.dumps(experience_vector),
                    r["id"],
                )

=======
            
            for r in results:
                skills_content = ','.join([f'{skill["name"]}:{skill["level"]}' for skill in json.loads(r["skills"])])
                skills_content = f"skills: {skills_content}"
                experience_content = ','.join([f'{experience["company"]}:{experience["position"]}' for experience in json.loads(r["experiences"])])
                experience_content = f"experience: {experience_content}"

                [skills_vector, experience_vector] = embed_contents([(skills_content), experience_content])

                await db.execute("""
                    UPDATE resumes SET vector_skills = $1, vector_experience = $2 WHERE id = $3
                """, json.dumps(skills_vector), json.dumps(experience_vector), r["id"])
            
>>>>>>> 386f40c1562c (wip)
        except Exception as e:
            click.echo(f"Error re-calculating vector skills: {e}")
            raise ConnectionError(f"Failed to re-calculate vector skills: {str(e)}")
        finally:
            await db.close()
<<<<<<< HEAD

    asyncio.run(re_calculate_vector_skills())


@cli.command()
def migrate():
    """Run database migrations."""
    asyncio.run(run_migrations())


=======
            
    asyncio.run(re_calculate_vector_skills())


>>>>>>> 386f40c1562c (wip)
if __name__ == "__main__":
    cli()
