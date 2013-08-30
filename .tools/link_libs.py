#!/usr/bin/env python

"""
Does the job of linking up the packages listed in requirements.txt and adding
them to the ``BASE_PATH`` directory for deploying to appspot.
"""

import os
import sys
import inspect

import pip
from pip.req import parse_requirements

BASE_PATH = os.environ.get('BASE_PATH', 'lib/external')


def get_required_packages(reqs_file):
    return [p.name for p in parse_requirements(reqs_file)]


def get_distributions(*packages):
    for installed_dist in pip.get_installed_distributions():
        if installed_dist.project_name not in packages:
            continue

        yield installed_dist


def get_toplevel_packages(distribution):
    """
    Returns all the top level packages in a distribution

    Wrap up the crappiness in a decent API.
    """
    egg_info_dir = os.path.join(
        distribution.location,
        '%s.egg-info' % (distribution.egg_name(),)
    )

    top_level = os.path.join(egg_info_dir, 'top_level.txt')

    with open(top_level, 'rt') as fp:
        for line in fp.readlines():
            yield line.strip()


def get_module_base_name(base_name):
    if base_name.endswith('.pyc'):
        base_name = base_name[:-1]

    if base_name.endswith('__init__.py'):
        return os.path.dirname(base_name)

    return base_name


def strip_base_dir(module_file_name, base_dir):
    assert module_file_name.startswith(base_dir)

    return module_file_name[len(base_dir):].strip(os.path.sep)


def get_package_dir(root_dir, package):
    """
    Yields the source dir of the package (relative to the root_dir).
    """
    # to absolutely know the source of the module, we import it
    sys.path.insert(0, root_dir)

    try:
        module = __import__(package)
    finally:
        sys.path.pop(0)

    try:
        module_file_name = inspect.getfile(module)
    except TypeError:
        # support for zope BS
        path = getattr(module, '__path__', None)

        if not path:
            raise StopIteration

        for module_file_name in path:
            base_name = strip_base_dir(
                module_file_name,
                root_dir
            )

            yield get_module_base_name(base_name)

        raise StopIteration

    base_name = strip_base_dir(module_file_name, root_dir)

    yield get_module_base_name(base_name)


def get_distribution_meta(*dists):
    """
    Returns a generator that will produce base_dir and package name tuples of
    the locations of the top level packages for each distribution
    """
    distributions = {}
    seen = set()

    for dist in get_distributions(*dists):
        distributions[dist.key] = dist
        seen.add(dist.project_name)

        for package in get_toplevel_packages(dist):
            for base_name in get_package_dir(dist.location, package):
                yield dist.location, base_name

    not_seen = seen.difference(dists)

    if not_seen:
        raise EnvironmentError('Distributions %r not found' % (
            ', '.join(not_seen)))


def _rmdir(dest_dir):
    """
    Removes a directory, supporting symlinks
    """
    if not os.path.exists(dest_dir):
        return

    try:
        os.unlink(dest_dir)
    except OSError:
        # probably a directory
        import shutil

        shutil.rmtree(dest_dir)


def ensure_symlink(location, module, dest_root=BASE_PATH):
    source_dir = os.path.join(location, module)
    dest_dir = os.path.join(dest_root, module)

    os.symlink(source_dir, dest_dir)


if __name__ == '__main__':
    if not os.path.exists(BASE_PATH):
        os.mkdir(BASE_PATH)

    for path in os.listdir(BASE_PATH):
        _rmdir(os.path.join(BASE_PATH, path))

    packages = get_required_packages('requirements.txt')

    for dir_name, base_name in set(get_distribution_meta(*packages)):
        ensure_symlink(dir_name, base_name)
