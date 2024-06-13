import os
import sys
from setuptools import setup, Extension, find_packages

# from setuptools.command.build_ext import build_ext as _build_ext

# 获取当前路径
current_path = os.path.abspath(os.path.dirname(__file__))

# 设置include_dirs和library_dirs路径
include_dirs = [current_path]
library_dirs = [current_path]

# 定义需要编译的扩展模块
extensions = [
    Extension(
        'thostmduserapi',
        sources=['thostmduserapi_wrap.cxx'],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        libraries=['thostmduserapi_se'],
    ),
    Extension(
        'thosttraderapi',
        sources=['thosttraderapi_wrap.cxx'],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        libraries=['thosttraderapi_se'],
    ),
]

# Setup function
setup(
    name='CTP_DH',
    version='1.0',
    description='CTP封装类',
    author='Your Name',
    packages=find_packages(),
    ext_modules=extensions,
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: C++'
    ]
)
