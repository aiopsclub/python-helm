#!/usr/bin/env python
# coding=utf-8

from setuptools import setup, find_packages

setup(
    name='python-helm',
    version="0.0.1",
    description=(
        'python client for helm'
    ),
    long_description=open('README.rst').read(),
    install_requires=[
        "gitpython==3.1.32",
        "grpcio==1.12.1",
        "grpcio-tools==1.12.1",
        "protobuf==3.18.3",
        "PyYAML>=4.2b1",
        "requests==2.19.1",
        "requests-oauthlib==0.8.0",
        "requestsexceptions==1.4.0",
        "supermutes==0.2.5"
        ],
    author='yxxhero',
    author_email='18333610114@163.com',
    maintainer='yxxhero',
    maintainer_email='<18333610114@163.com',
    license='Apache License 2.0',
    packages=find_packages(),
    platforms=["all"],
    url='https://github.com/yxxhero/python-helm',
    classifiers=[
        'Development Status :: 1 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache License 2.0',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries'
    ],
)
