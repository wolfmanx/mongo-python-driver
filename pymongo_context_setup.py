import sys
import os
import shutil

here = os.path.abspath(os.path.dirname(__file__))

if not os.path.isdir('pymongo_context'):
    os.mkdir('pymongo_context')
if not os.path.isdir('pymongo_context/pymongo_context'):
    os.mkdir('pymongo_context/pymongo_context')
    
shutil.copyfile('README-context-extension.rst', 'pymongo_context/README.txt')
shutil.copyfile('pymongo_context.py', 'pymongo_context/pymongo_context/__init__.py')
shutil.copyfile('waste_of_time.py', 'pymongo_context/waste_of_time.py')
shutil.copyfile('bson/context.py', 'pymongo_context/pymongo_context/bson_context.py')
os.chdir('pymongo_context')

sf = open('setup.py', 'w')
sf.write("""
from distutils.core import setup

setup(name='pymongo_context',
      version='0.1',
      description='PyMongo Context Extension Patcher',
      long_description='''
- import pymongo_context
- See waste_of_time.py for an example.''',
      license='Apache License',
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Database",
        ],
      author='Wolfgang Scherer',
      author_email='Wolfgang.Scherer@gmx.de',
      url='https://github.com/wolfmanx/mongo-python-driver',
      keywords='MongoDB BSON',
      packages=['pymongo_context'],
      )
""")
sf.close()

mf = open('MANIFEST.in', 'w')
mf.write('''
include README.txt
include waste_of_time.py
''')
mf.close()

os.system('python setup.py ' + ' '.join(sys.argv[1:]))
