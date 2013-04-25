from distutils.core import setup


setup(
    name='annotation',
    description='TODO',
    long_description=open('README.md').read(),
    version='0.1',
    author='Alex Buchanan',
    author_email='buchanae@gmail.com',
    license='Apache',
    py_modules=['annotation'],
    dependency_links=['http://github.com/abuchanan/interval/tarball/master#egg=abuchanan_interval-0.1'],
    install_requires=['more_itertools', 'abuchanan_interval==0.1'],
)
