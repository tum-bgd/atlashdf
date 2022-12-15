from glob import glob
from setuptools import setup
import pybind11
from pybind11.setup_helpers import Pybind11Extension
import sys
jq= ["src/builtin.c","src/bytecode.c","src/compile.c","src/execute.c",
     "src/jq_test.c","src/jv.c","src/jv_alloc.c","src/jv_aux.c",
     "src/jv_dtoa.c","src/jv_file.c","src/jv_parse.c","src/jv_print.c",
     "src/jv_unicode.c","src/linker.c","src/locfile.c","src/util.c",
     "src/decNumber/decContext.c","src/decNumber/decNumber.c",
     "src/jv_dtoa_tsd.c"]
jq = ["jq/%s"%(x) for x in jq]



ext_modules = [
    Pybind11Extension(
        "atlashdf",
        sorted(list(glob("src/*.cpp")) + ["../atlashdf/osm_immediate.cpp",'src/jq_shield.c']) ,  # Sort source files for reproducibility
        include_dirs=['./src','../atlashdf', '../include', '/usr/include/hdf5/serial','./jq/src'],
        library_dirs=["/usr/lib/x86_64-linux-gnu/hdf5/serial", "./jq/.libs","./jq/modules/oniguruma/src/.libs" ],
        libraries=["hdf5"],
        extra_compile_args=["-DHAVE_JQ"],
        extra_link_args=["-lprotobuf-lite", "-losmpbf", "-lz"],# + ["-ljq","-lonig"], ","","","","","","","","",
        extra_objects=["./jq/.libs/libjq.a","./jq/modules/oniguruma/src/.libs/libonig.a"]
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
    package_data={'onig': ['libonig.so.4']},

    # add custom build_ext command
    #cmdclass=dict(build_ext=CMakeBuild),
    #zip_safe=False,
)

#setup(
#    ...,
#    ext_modules=ext_modules
#)
