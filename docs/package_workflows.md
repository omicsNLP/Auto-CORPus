HTML Logic

``` mermaid
flowchart TD
    A[Start] --> B[Parse Arguments]
    
    
    B --> X[Read Config]
    X --> Y[Read Input File]
    Y --> AA[Validate Input File]
    
    AA -->|Valid| AB[Soupify Input File]
    AA -->|Invalid| AC[Handle Error] --> Z
    
    AB --> AD[Clean Text]
    AD --> AE[Extract Keywords]
    AE --> AF[Extract Title]
    AF --> AG[Extract Sections]
    AG --> AH[Extract Text]
    AH --> AI[Set Unknown Section Headings]
    AI --> AJ[Handle HTML]
    AJ --> AK[Merge Table Data]
    AK --> AL[Convert to BioC]
    
    AL --> AM[Output BioC JSON]
    AL --> AN[Output BioC XML]
    AL --> AO[Output Tables to BioC JSON]
    AL --> AP[Output Abbreviations to BioC JSON]
    AL --> AQ[Output to JSON]
    AL --> AR[Output to Dictionary]
    
    AM --> Z
    AN --> Z
    AO --> Z
    AP --> Z
    AQ --> Z
    AR --> Z
    
    Z[End]
```