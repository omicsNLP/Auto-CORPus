**Data element types**

The `data` entities within the config file sections allows Auto-CORPus to parse details out of the sections, such as the section
header, table title or footer. Some of the defined `data` entity elements are required to allow Auto-CORPus to parse source HTML files
correctly.

Sections which do not make use of the `data` entity:

- Title
- Keywords
- paragraphs
- abbreviations-table

All other sections make use of the `data` entity. The following sections and corresponding `data` entities are required by Auto-CORPus:

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

In addition, the References section does not require any entries within the `data` entity to function correctly, but does allow
the use of:
  - title
  - journal
  - volume

Some HTML source files include markup within the reference text to identify the above information. The inclusion
of these `data` entries in the config will enable Auto-CORPus to identify and process this information and include it in the output file.

