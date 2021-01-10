import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pwiki",
    version="0.0.2",
    author="Fastily",
    author_email="fastily@users.noreply.github.com",
    description="A Python library for effortlessly interacting with Wikipedia/MediaWiki",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fastily/pwiki",
    include_package_data=True,
    packages=setuptools.find_packages(),
    install_requires=['requests'],
    classifiers=[
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
