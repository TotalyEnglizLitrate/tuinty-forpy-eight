from setuptools import setup

with open("readme.md", "r") as desc:
    long_description = desc.read()

setup(name='tuinty-forpy-eight',
      version='1.3.1',
      description='A tui implementation of the game "2048", made with textual',
      long_description=long_description,
      long_description_content_type="text/markdown",
      entry_points={'console_scripts' : '2048 = tuinty_forpy_eight.main:main'},
      package_data={'tuinty_forpy_eight': ['2048.tcss', '2048.md']},
      url='https://github.com/TotalyEnglizLitrate/tuinty-forpy-eight',
      author='TotalyEnglizLitrate',
      packages=['tuinty_forpy_eight'],
      install_requires=['textual >= 0.39.0'])
