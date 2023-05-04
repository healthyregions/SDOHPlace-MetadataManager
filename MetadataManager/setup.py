from setuptools import setup

setup(
    name='MetadataManager',
    packages=['manager'],
    include_package_data=True,
    install_requires=[
        'Flask',
        'Flask-Cors',
        'Flask-SQLAlchemy',
        'pysolr',
        'python-dotenv',
    ],
)