from setuptools import setup, find_packages

setup(
    name="akasha-lang",
    version="0.1.0",
    description="Akasha — The Telugu-inspired Programming Language & PC Compiler",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Akasha Team",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "akasha.web": ["static/*"],
    },
    entry_points={
        "console_scripts": [
            "akasha=akasha.cli.astra:main",
            "akashac=akasha.cli.compiler_cli:main",
            "akasha-ide=akasha.ide.app:launch_ide",
        ],
    },

    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Interpreters",
    ],
)
