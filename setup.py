# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 11:30:00 2020

@author: Martin
"""
import setuptools

setuptools.setup(
    name="pygeonica", # Replace with your own username
    version="0.1",
    url='http://github.com/isi-ies-group/pygeonica',
    author="Martin",
    author_email="m.nenkov@alumnos.upm.es",
    description="Pequeña librería que facilita la lectura de canales de una unidad Meteodata y de la base de datos de Geonica Suite 4K",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Windows",
    ],
    python_requires='>=3.6',
    packages=['pygeonica'],
    zip_safe=False,
    package_data={'': ['*.txt','*.yaml']},
    include_package_data=True,
)
