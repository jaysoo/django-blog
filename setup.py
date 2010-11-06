from setuptools import find_packages

__author__ = 'jack.hsu@gmail.com'
__version__ = '1.0'

METADATA = dict(
    name = 'django-blog',
    version = __version__,
    url = 'http://github.com/jaysoo/django-blog',
    description ='Simple blog app for Django',
    author = 'Jack Hsu',
    author_email = 'jack.hsu@gmail.com',
    packages = find_packages(),
    license = 'The MIT License',
    keywords = 'twitter django blog',
    zip_safe = False,
)

SETUPTOOLS_METADATA = dict(
    install_requires = ['setuptools', 'django_wysiwyg', 'django_twitter'],
    include_package_data = True,
)

def Read(file):
    return open(file).read()

def BuildLongDescription():
    return '\n'.join([Read('LICENSE'), Read('README.md')])

def Main():
    # Build the long_description from the README and CHANGES
    METADATA['long_description'] = BuildLongDescription()

    # Use setuptools if available, otherwise fallback and use distutils
    try:
        import setuptools
        METADATA.update(SETUPTOOLS_METADATA)
        setuptools.setup(**METADATA)
    except ImportError:
        import distutils.core
        distutils.core.setup(**METADATA)

if __name__ == '__main__':
    Main()
