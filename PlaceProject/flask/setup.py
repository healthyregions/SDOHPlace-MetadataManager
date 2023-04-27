from setuptools import setup

setup(
    name='PlaceProject',
    packages=['app'],
    include_package_data=True,
    install_requires=[
        'Flask',
        'Flask-Cors',
        'Flask-SQLAlchemy',
        'pysolr',
        'python-dotenv',
    ],
)