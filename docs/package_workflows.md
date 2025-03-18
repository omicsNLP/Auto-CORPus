# HTML Logic

``` mermaid
flowchart TD

    classDef Autocorpus  fill:lightblue, stroke:black;
    classDef TODO fill:orange, stroke:black;
    classDef __main__ fill:lightgreen, stroke:black;

    subgraph Legend[Classes/Files]
        legend_autocorpus[Autocorpus]:::Autocorpus
        legend_main[__ main __.py]:::__main__
        legend_todo[placeholder function]:::TODO
    end


    A[Start]:::__main__ --> B[Parse Arguments]:::__main__
    B --> read_file_structure[read file structure]:::__main__

    read_file_structure --> X[Read Config]:::Autocorpus
    X --> validate_config

    validate_config:::TODO --> Y[Read Input File]:::Autocorpus
    Y --> AA[Validate Input File]:::TODO
    AA -->|Valid| AB[Soupify Input File
    >Autocorpus:42]:::Autocorpus
    AA -->|Invalid| AC[Handle Error]:::Autocorpus

    AB --> AJ[Handle HTML
    >Autocorpus:394]:::Autocorpus
          AJ --> ExtractText

    subgraph ExtractText[Extract Text]
        AH[Extract Text
    >Autocorpus:395]:::Autocorpus --> get_title[Get Title
    >Autocorpus:123]:::Autocorpus
        get_title --> get_keywords[Get Keywords
        >Autocorpus:107]:::Autocorpus
        get_keywords --> get_sections[Get Sections
        >Autocorpus:133]:::Autocorpus
        get_sections --> set_unknown_headings[Set Unknown Headings
        >Autocorpus:183]:::Autocorpus
    end


    ExtractText --> AL{Convert to BioC}:::Autocorpus

    AL --> AM[Output BioC JSON]:::Autocorpus
    AL --> AN[Output BioC XML]:::Autocorpus
    AL --> AO[Output Tables to BioC JSON]:::Autocorpus
    AL --> AP[Output Abbreviations to BioC JSON]:::Autocorpus
    AL --> AQ[Output to JSON]:::Autocorpus
    AL --> AR[Output to Dictionary]:::Autocorpus
```
