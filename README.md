# Pupil Labs Real-Time Python API Client

[![ci](https://github.com/pupil-labs/pl-realtime-api/actions/workflows/main.yml/badge.svg)](https://github.com/pupil-labs/pl-realtime-api/actions/workflows/main.yml)
[![documentation](https://img.shields.io/badge/docs-mkdocs-708FCC.svg?style=flat)](https://pupil-labs.github.io/pl-realtime-api/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre_commit-black?logo=pre-commit&logoColor=FAB041)](https://github.com/pre-commit/pre-commit)
[![pypi version](https://img.shields.io/pypi/v/pupil-labs-realtime-api.svg)](https://pypi.org/project/pupil-labs-realtime-api/)
[![python versions](https://img.shields.io/pypi/pyversions/pupil-labs-realtime-api)](https://pypi.org/project/pupil-labs-realtime-api/)

`pupil_labs.realtime_api` is a Python module that wraps around the [Pupil Labs Real-Time Network API](https://github.com/pupil-labs/realtime-network-api) while offering some convenience functions sucha as gaze ↔ frame matching, and exposing easy-to-use functions and classes to get started without having to know much about advanced programming or network communication!

## Installation

```sh
pip install pupil-labs-realtime-api
# pip install -e git+https://github.com/pupil-labs/pl-realtime-api.git # from source
```

If you want to run the examples, you can install the package with the `examples` extra dependencies:

```sh
pip install "pupil-labs-realtime-api[examples]"
# uv pip install pupil-labs-realtime-api --group examples # using uv
```

> [!IMPORTANT]
> This package is only available for Pupil Invisible and Neon, Pupil Core uses a different API.
> If you’re working with Pupil Core, please refer to the [Pupil Core Network API](https://docs.pupil-labs.com/core/developer/network-api/) if you need streaming capabilities.

📚 Check out the [documentation here](https://pupil-labs.github.io/pl-realtime-api)
