
import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="general_robotics_toolbox", # Replace with your own username
    version="0.1.1",
    author="John Wason",
    author_email="wason@wasontech.com",
    description="General robotics toolbox developed by RPI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rpiRobotics/rpi_general_robotics_toolbox_py",
    packages=setuptools.find_packages("src"),
    package_dir={"" :"src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["numpy"],
    python_requires='>=2.7',
    tests_require=['pytest'],
    extras_require={
        'test': ['pytest']
    }
)