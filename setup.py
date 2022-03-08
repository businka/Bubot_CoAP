import setuptools

setuptools.setup(
    name='Bubot_CoAP',
    version='1.0.4',
    license='MIT',
    author='Razgovorov Mikhail',
    author_email='1338833@gmail.com',
    url="https://github.com/businka/Bubot_CoAP.git",
    description='python library to the CoAP protocol.',
    install_requires=[
        'cbor2',
        'aio_dtls'
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
)
