from setuptools import setup, find_packages

setup(
    name='wasapflow-bridge',
    version='1.3.0',
    description='Official Python SDK for WasapFlow Bridge — WhatsApp Cloud API via WasapFlow Tech Provider',
    author='WasapFlow',
    license='MIT',
    packages=find_packages(),
    install_requires=['requests>=2.28.0'],
    python_requires='>=3.8',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
