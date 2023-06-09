from setuptools import setup, find_packages
from pathlib import Path
import os

if __name__ == "__main__":
    with Path(Path(__file__).parent, "README.md").open(encoding="utf-8") as file:
        long_description = file.read()

    def _read_reqs(relpath):
        fullpath = os.path.join(os.path.dirname(__file__), relpath)
        with open(fullpath) as f:
            return [s.strip() for s in f.readlines() if (s.strip() and not s.startswith("#"))]

    REQUIREMENTS = _read_reqs("requirements.txt")

    setup(
        name="distcompute-client",
        packages=find_packages(),
        include_package_data=True,
        package_data={'': ['*.jar', '*.gz', '*.mdb']},
        version="1.0.0",
        license="MIT",
        description="A multi-stage distributed compute tracker and job manager.",
        long_description=long_description,
        long_description_content_type="text/markdown",
        author="Theo Coombes",
        author_email="theocoombes06@gmail.com",
        url="https://github.com/TheoCoombes/distcompute-client",
        data_files=[(".", ["README.md"])],
        keywords=["distributed computing", "cluster", "worker swarm", "job management"],
        install_requires=REQUIREMENTS,
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Topic :: System :: Distributed Computing",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3.8",
        ],
    )
