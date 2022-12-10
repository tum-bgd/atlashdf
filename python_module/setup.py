from glob import glob
from setuptools import setup
import pybind11
from pybind11.setup_helpers import Pybind11Extension

ext_modules = [
    Pybind11Extension(
        "atlashdf",
        sorted(glob("src/*.cpp")),  # Sort source files for reproducibility
        #extra_link_args=[""],
    ),
]

setup(
    name='atlashdf',
    version='0.1',
    author='Martin Werner',
    author_email='martin.werner@tum.de',
    description='Follows',
    long_description='',
    # add extension module
    ext_modules=ext_modules,
    # add custom build_ext command
    #cmdclass=dict(build_ext=CMakeBuild),
    #zip_safe=False,
)

#setup(
#    ...,
#    ext_modules=ext_modules
#)
