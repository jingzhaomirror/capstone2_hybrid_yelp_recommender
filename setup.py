from distutils.core import setup

def readme():
    """Import the README.md Markdown file and try to convert it to RST format."""
    try:
        import pypandoc
        return pypandoc.convert('README.md', 'rst')
    except(IOError, ImportError):
        with open('README.md') as readme_file:
            return readme_file.read()

setup(
    name='yelp_recommender',
    version='0.1',
    description='hybrid restaurant recommender system for yelp',
    long_description=readme(),
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    url='https://github.com/jingzhaomirror/Springboard_capstone_2',
    author='jingzhaomirror',
    author_email='jingzhaomirror@gmail.com',
    license='MIT',
    packages=['yelp_recommender'],
)
