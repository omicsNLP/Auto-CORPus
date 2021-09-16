Data elements in further detail

[If possible make all sections use the optional elements as well]

There are two categories of data-elements, these are:

- "soft" required
- optional

There are no required data elements within AC.

The config validator could point out missing "soft" required elements though if I ever make one.

The "soft" required elements are not required for AC to process a file but the output will be incomplete if not
provided. In some situations this could be desired, such as a publisher which provides tables as images, therefore the
table `data` element of `table-content` found within config_pmc.json is meaningless when processing files as there will
be no table content.

The optional elements are found in sections where publishers may or may not add HTML tags around certain
information. The only section which makes use of this currently is the `references` section where PMC occasionally
adds HTML tags around the paper title, journal and volume (and possibly more). AC will look for these elements and if found will include 
them in the output file explicitly, if not found then the full reference text will still be output, which should include
the title/journal/volume but these will need to be parsed from the text outside of AC.

If a publisher does not provide any info tags within the references or you are
not interested in AC extracting this information then `references->data` can be left empty.

Sections which do not make use of the `data` entry:

- Title
  - source HTML title
- Keywords
  - source HTML key words section
- paragraphs
  - a single paragraph within the source HTML
- abbreviations-table
  - Abbreviations table defined within the source HTML

Sections which make use of the `data` entry:
- References
  - references section of the source HTML
  - Uses optional elements only:
    - title
    - journal
    - volume
    - any user entered value
- Sections
  - A top level section within the source HTML, such as the abstract or introduction
  - Uses "soft" required elements
    - headers
- Sub-sections
  - A sub-section of a section. Such as objectives within the abstract
  - Sub-sections will be looked for within all found sections, if there is no config to find sections 
  then sub-sections will not be looked for.
  - Uses "soft" required elements
     - headers
- Tables
  - The top level container for a table within the source HTML, this should contain the table title, caption etc. as well as
  the table contents.
  - uses "soft" required elements
    - caption
    - table-content
    - title
    - footer
    - header-row
    - header-element
    - body-row
    - body-element
- Figures
  - Figures are not processed by AC, by providing this config AC will remove any figure captions/headers etc.
  from the final output.
  - uses "soft" required elements:
    - caption
    - title
    - footer

