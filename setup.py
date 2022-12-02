from setuptools import setup


setup(
    name="ip2w",
    version="0.0.1",
    description="Otus weather uWSGI daemon",
    author="Alexey Zateev",
    author_email="z1195522@gmail.com",
    license="BSD",
    install_requires=[
        "requests>=2.18.4,<2.28",
        "uwsgi",
        "ipinfo<=3.0.0",
    ],
    project_urls={
        "Source": "https://github.com/z-lex/otus-ip2w-daemon",
    },
    python_requires=">=3.6",
)
