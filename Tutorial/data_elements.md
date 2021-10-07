The data sub-sections within the config file sections allows AC to parse details out of the sections, such as the section
header, table title or footer. Some of the defined data sub-section elements are required to allow AC to parse a paper
correctly,

Sections which do not make use of the `data` entry:

- Title
- Keywords
- paragraphs
- abbreviations-table

All other sections make use of the `data` sub-section, below is a list of the sections and the data subsections which
are needed to be filled in to allow AC to work correctly.
- References
- Sections
  - headers
- Sub-sections
  - headers
- Tables
  - caption
  - table-content
  - title
  - footer
  - table-row
  - header-row
  - header-element
- Figures
  - caption

The `references` section does not require any entries within the data sub-section to function correctly but does allow
the use of:
- title
- journal
- volume

Some publishing groups will wrap parts of the reference text within tags to identify the above information, the inclusion
of these data entries will add the parsed info to the output as a seperate key:value pair.

