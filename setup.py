from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='maml',
      version=version,
      description="Mako Abstract Markup Language",
      long_description="""\
HAML-alike for Mako""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='Mako HTML Haml Markup Template',
      author='Brian Hawthorne',
      author_email='hawthorne@amyris.com',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
