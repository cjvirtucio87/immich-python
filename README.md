# immich-python

## Introduction

This is a fork of [immich-ruby](https://github.com/chengguangnan/immich-ruby), re-written in python. Instructions and functionality are the same, except you need to have python and [astral-sh/uv](https://github.com/astral-sh/uv) installed, and that the script is executed with [./run.sh]

## Motivation

I just don't like ruby.

## Configuration

Define authentication configuration at `"${HOME}/.config/immich/auth.yml"`:

```yaml
---
instanceUrl: http://immich.local:2283
apiKey: <api key>
```

## Usage

```console
./run.sh --album <album name>
```

Content will be written to the `downloads` folder in this repository (it will be gitignored).




