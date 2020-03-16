# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 11:30:00 2020

@author: Martin
"""
import setuptools

setuptools.setup(
    name="geonica-app", # Replace with your own username
    version="0.1",
    url='http://github.com/m-nenkov/geonica-app',
    author="Martin",
    author_email="m.nenkov@alumnos.upm.es",
    description="Pequeña librería que facilita la lectura de la base de datos geonica",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Windows",
    ],
    python_requires='>=3.6',
    packages=['geonica-app'],
    zip_safe=False,
    package_data={'': ['*.txt','*.yaml']},
    include_package_data=True,
)
