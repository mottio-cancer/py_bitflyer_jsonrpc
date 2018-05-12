# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='py_bitflyer_jsonrpc',
    packages=['py_bitflyer_jsonrpc'],
    version='0.0.1',
    description="Python wrapper for bitFlyer's JSON-RPC(WebSocket) API",
    long_description=readme,
    author='Mottio Cancer',
    author_email='mottio.cancer@gmail.com',
    url='https://github.com/mottio-cancer/py_bitflyer_jsonrpc',
    install_requires=['websocket'],
    keywords=["bitcoin", "bitflyer", "wrapper", "JSON-RPC API", "websocket"],
    license=license
)

