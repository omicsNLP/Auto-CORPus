from setuptools import setup

with open("README.md", "r") as fh:
	long_description = fh.read()

setup(
	name="autoCORPus",
	version='0.0.1',
	description="autoCORPus",
	py_modules=["autoCORPus"],
	package_dir={'': 'src'},
	install_requires=[
		"beautifulsoup4==4.9.3",
		"soupsieve==2.2.1"
	],
	extras_require={
		"dev":[
			"pytest>=3.7"
		]
	}
)