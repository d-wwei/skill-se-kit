from setuptools import find_packages, setup


setup(
    name="skill-se-kit",
    version="0.1.0",
    description="Protocol-compatible Skill-SE-Kit runtime for self-evolving skills",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
)
