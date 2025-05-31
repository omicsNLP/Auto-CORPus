# Test data for Auto-CORPus

This folder contains data for regression tests. It is divided into public and private, depending on whether the files' licences permit redistribution.

## Private data

The private data is only available to members of the [omicsNLP organisation], though you can still run the other regression tests without it.

[omicsNLP organisation]: https://github.com/omicsNLP

### Downloading the data

The data is housed in a [git submodule]. To download the data, run:

```sh
git submodule update --init
```

[git submodule]: https://git-scm.com/book/en/v2/Git-Tools-Submodules

### Adding new test data

Data must be committed to the `main` branch of the [Auto-CORPus-private-test-data] repository and pushed, so that it is available to other developers and the GitHub runners. (You can do this directly from the submodule directory.) The data should be structured as described in the section below.

Once you have updated the private test data repository, you will also need to update the commit that the submodule points to in the main repository (this one) before making a pull request:

```sh
# Update submodule
cd tests/data/private
git checkout main
git pull

# Make commit in main repo
cd ../../..
git add tests/data/private
git commit -m "Obtain new private data"
```

[Auto-CORPus-private-test-data]: https://github.com/omicsNLP/Auto-CORPus-private-test-data

## Structure of data

The `public` and `private` subfolders are each structured in the same way.

Currently only data for HTML tests is provided and it is in a folder called `html`. Within that folder, there are subfolders whose names **must** correspond to a [`DefaultConfig`] (e.g. `LEGACY_PMC`). The subfolders contain the test data (i.e. HTML files) along with the expected output files (i.e. `*_bioc.json`, `*_abbreviations.json` and, optionally, `*_tables.json`). If you add new test data, you must add the corresponding output files at the same time.

For example, at the time of writing, the structure of `tests/data` looks like this:

```txt
tests/data/
├── private
│   └── html
│       └── PMC
│           ├── PMC10071775_abbreviations.json
│           ├── PMC10071775_bioc.json
│           ├── PMC10071775.html
│          (...)
└── public
    └── html
        ├── LEGACY_PMC
        │   ├── PMC8885717_abbreviations.json
        │   ├── PMC8885717_bioc.json
        │   ├── PMC8885717.html
        │   └── PMC8885717_tables.json
        └── PMC
            ├── PMC8885717_abbreviations.json
            ├── PMC8885717_bioc.json
            ├── PMC8885717.html
            └── PMC8885717_tables.json
```

[`DefaultConfig`]: https://omicsnlp.github.io/Auto-CORPus/reference/autocorpus/configs/default_config/#autocorpus.configs.default_config.DefaultConfig