import click
import asyncio

from javis.injest import resume


cli = click.Group()


@cli.command()
@click.argument('folder', type=click.Path(exists=True))
def ingest_resume(folder: str):
    """Ingest a resume into the database."""
    asyncio.run(resume.main(folder))


if __name__ == '__main__':
    cli()
