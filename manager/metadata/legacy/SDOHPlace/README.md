# Compiling Data Dictionaries

This directory will serve as a place for us to begin collecting more granular, study data-level information about each dataset in our project. This will allow us to track what variables were used in the calculation of each index, for example, and will allow users to make connections through that information. "What indices use unemployment statistics?"

## Tasks

For each of our main datasets, we'd like to begin collecting a list of variables used, methods terminology, and other related information. Essentially, this will be an organized version of each study's data dictionary/methodology, which we already link to in the existing Aardvark-based markdown records (see `../Metadata/`).

1. Create a new markdown file for each record (already started)
    Note: We may need to have multiple files for different years or different spatial resolutions of the same study, *if* the relevant information differs between years. Otherwise, a single file is fine.
2. Add links to relevant web resources for data dictionary/methods, etc. under the **Resources** header
3. Begin pulling information from those resources under the following headers
    - **Resource Type**
        Index, Ranking, or Data Collection (still working out these terms, suggestions welcome...)
    - **Methods Variables**
        Find this info in the methods or data dictionary documentation. Pasting in a simple list is good enough for now, we can worry about exact format later.
    - **Data Variables**
        The names/titles of data that is available in this dataset, e.g. column headers a spreadsheet. It would be best to pair column headers with pretty labels, for example "avg_age/Average Age"
    - **Anything Else?**
        Feel free to add notes or your thoughts about each dataset in this final section.

## Next Steps

Once we have a large amount of this information in one place, we'll be able to start looking through it and decide how to link variables between different studies, combine terminology, etc.