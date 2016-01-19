from setuptools import setup, find_packages

setup(name='pygame_maker',
    version='0.1',
    description='ENIGMA-like pygame-based game engine',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: GNU Lesser General Public License v2 (LGPGv2)',
        'Progamming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: pygame',
    ],
    keywords='pygame engine',
    url='http://github.com/rlc2/pygame_maker',
    author='Ron Lockwood-Childs',
    author_email='rlc2@dslextreme.com',
    license='LGPL v2.1',
    packages=[
        'pygame_maker',
        'pygame_maker.actions',
        'pygame_maker.actors',
        'pygame_maker.events',
        'pygame_maker.logic',
        'pygame_maker.scenes',
        'pygame_maker.sounds',
        'pygame_maker.support',
    ],
    package_data = {
        '': ['script_data/*.png','script_data/*.wav','script_data/*.yaml','script_data/*.tmpl']
    },
    scripts = [
        'scripts/pygame_maker_app.py'
    ],
    install_requires=[
        'numpy>=1.10.1',
        'yaml>=3.11',
        'pyparsing>=2.0.5',
        'pygame>=1.9.0',
    ],
    zip_safe=False)
