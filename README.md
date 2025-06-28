# immich-python

## Introduction

This is a fork of [immich-ruby](https://github.com/chengguangnan/immich-ruby), re-written in python. Instructions and functionality are the same, except for the following:

1. you need to have python installed
1. generate a virtual environment with:
    ```console
    python -m venv .venv
    ```
1. activate the venv with:
    ```console
    . .venv/bin/activate
    ```
1. install requirements with:
    ```console
    python -m pip install -r requirements.txt
    ```

## Motivation

I just don't like ruby.

## Usage

```
python immich.py -a Hawaii
```

This script will connect to the Immich defined at ~/.config/immich/auth.yml. 

```
instanceUrl: http://immich.local:2283
apiKey: 
```

Use `-a` to set the Album you want to export.

The code exports photos by 3 steps:

1. Download each assets by zip
2. Unzip them
3. Rename assets based on EXIF

The final results is in "downloads/:album_name/flatten/"




