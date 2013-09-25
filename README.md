TrendBlotter
=========
This is what's making waves.

Getting Started
---------------
Clone the repo.

```
git clone https://github.com/tylertreat/TrendBlotter.git
````

Ensure that pip is installed.

- http://www.pip-installer.org/en/latest/

We highly recommend using a virtual environment (virtualenv) to ease
development.

- http://www.virtualenv.org/en/latest/

To help make working with virtualenv even easier we recommend checking out
virtualenvwrapper.

- http://virtualenvwrapper.readthedocs.org/en/latest/
- Then you can cd to your directory.
  - Create your virtualenv and point it to your current directory

    ```
    mkvirtualenv blotter -a $PWD
    ```

  - From then on when you activate your virtualenv it will take you to your
      directory.

    ```
    workon blotter
    ```


To install all dependencies and correctly wire up lib for GAE deployment:

```
sudo make deps
```

- This will pip install all the libraries referenced in requirements.txt and
requirements\_dev.txt. All of the libraries within requirements.txt will also
get symlinked into a lib directory. This will allow those libraries to be
deployed to GAE.


Install a path configuration file in the virtualenv so you can use the 
appengine's runtime environment.

- Create a `gae.pth` file in your virtual env site-packages directory. 
  `/path/to/google_appengine` should be the install location of the Google 
  AppEngine SDK. For example, `/usr/local/google_appengine`. 

  If you have created the symlinks for the App Engine SDK:
```
workon blotter
dirname $(readlink `which dev_appserver.py`) >> $VIRTUAL_ENV/lib/python2.7/site-packages/gae.pth
echo 'import dev_appserver; dev_appserver.fix_sys_path()' >> $VIRTUAL_ENV/lib/python2.7/site-packages/gae.pth
```

You should now be able to launch a Python interactive shell (with your 
virtualenv activated) and `import google.appengine`.

```
$ python
Python 2.7.3 (v2.7.3:70274d53c1dd, Apr  9 2012, 20:52:43)
[GCC 4.2.1 (Apple Inc. build 5666) (dot 3)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import google.appengine
>>>
```


---

Commands
--------

### Tests ###

*Unit tests*

```
make unit
```

- The unit tests just run the basic nosetests using all the configuration from
the setup.cfg. By default we skip the tests marked with slow. To run the
slow tests as well you need to run the integration tests shown below.

You could also just as easily run:

```
nosetests
```
    
*Integration tests*

```
make test
```

- This will run all the tests including the slow ones. By default we are
ignoring all logs below ERROR level. You can switch this to whatever you
prefer when needed. NDB outputs a ton of debugging level logs which makes it
quite difficult to debug when you do hit errors in your tests. This will
also clean out all your pyc files before running the tests to ensure running
from a good state.

or

```
make integrations
```

- This will run the same as above just without cleaning the pyc files.

or

```
nosetests --logging-level=ERROR -a slow
```

- This is the command that integrations is wrapping.


### Running the development environment. ###

To run the development environment you can run:

```
make run
```

- This runs the dev app server on the default port.
This command also runs all dependency checks and installs any missing
libraries.

You can also just run:

```
dev_appserver.py .
```

- This will no do any of the dependency checks.


### Environment ###

To install all of the projects dependencies run:

```
make deps
```

To clean the dist logs:

```
make distclean
```

To update just the deployment dependencies:

```
make py_deploy_deps
```

To update just the development dependencies:

```
make py_dev_deps
```

---

NOTICE
------
Requirements to commit here:
  
  - Branch off master, PR back to master.
  - Your code should pass [Flake8](https://github.com/bmcustodio/flake8).
  - Unit test coverage is required.
  - Good docstrs are required.
  - Good [commit messages](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html) are required.
