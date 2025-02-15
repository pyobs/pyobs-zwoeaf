from pybind11.setup_helpers import Pybind11Extension, build_ext


def build(setup_kwargs):
    ext_modules = [
        Pybind11Extension(
            "pyobs_zwoeaf/pybind_wrapper",
            ["pyobs_zwoeaf/pybind_wrapper.cpp"],
            extra_objects=["lib/lib/x64/libEAFFocuser.a"],
            extra_compile_args=["-O3", "-Wall", "-shared", "-fPIC", "-m64"],
            libraries=["rt", "udev", "pthread"],
            language="c++",
            cxx_std=11,
        )
    ]
    setup_kwargs.update(
        {
            "ext_modules": ext_modules,
            "cmd_class": {"build_ext": build_ext},
            "zip_safe": False,
        }
    )


# // compile with c++ -O3 -Wall -shared -std=c++11 -fPIC $(python3 -m pybind11 --includes)
# eaf_pybind_wrapper.cpp -o eaf_pybind_module$(python3-config --extension-suffix) -m64 -lrt
# -ludev ../lib/x64/libEAFFocuser.a -I ../include -m64 -lrt -ludev -lpthread
