from fabric.api import *
import os
 
  
def build_windows_dist():
    if os.name == 'nt':
        # Call the pyinstaller
        local("python ../pyinstaller/pyinstaller.py pypdfocr_windows.spec --onefile")

def prep_release():
    # Build the documentation
    # Convert the README.md to README.rst
    local("pandoc README.md -f markdown -t rst -o README.rst")

def run_tests():
    test_dir = "test"
    with lcd(test_dir):
        local("py.test -v --cov=pypdfocr --cov-report=term --cov-report=html")

def push_docs():
    """ Build the sphinx docs from develop
        And push it to gh-pages
    """
    githubpages = "/Users/virantha/dev/githubdocs/pypdfocr"
    with lcd(githubpages):
        local("git checkout gh-pages")
        local("git pull origin gh-pages")
    with lcd("docs"):
        print("Running sphinx in docs/ and building to ~/dev/githubpages/pypdfocr")
        local("make clean")
        local("make html")
    with lcd(githubpages):
        local("git add .")
        local('git commit -am "doc update"')
        local('git push origin gh-pages')

