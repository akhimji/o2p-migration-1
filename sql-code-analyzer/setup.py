from setuptools import setup, find_packages

setup(
    name='sql-code-analyzer',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A modular Python application to scan source code repositories for SQL queries and analyze tech stack components.',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'sqlparse',  # For SQL parsing and normalization
        'pyyaml',    # For YAML configuration parsing
        'regex',     # For advanced regex operations
        # Add other dependencies as needed
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)