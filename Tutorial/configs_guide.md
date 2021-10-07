We will use config_pmc.json as the example config for this guide.

The configs file is how you tell AC where to look for certain key elements of the article within the source HTML. We 
have provided 3 example configs for pubmed central, nature genetics and plos genetics. Additional configs for different
publishing groups can be created by following these examples and using the template config file.

All sections within the template config file should be present in all user defined configs to avoid errors. 

It is better to leave the `data` and `defined-by` sections blank if you do not want AC to process them instead of 
deleting the section. 

Each section must contain a `defined-by` sub-section but the `data` sub-section is optional. Omitting the `data` 
sub-section may result in that section not being processed properly.

```
{
    "section":{
        "defined-by":[],
        "data":{}
    }
}
```

The `defined-by` sub-section provides a listof HTML tags and attributes which AC can utilise to find ocurrences of the 
section within the source HTML. 
```
{
    "section":{
        "defined-by":[
            {
                "tag":"",
                "attrs":""
            }
        ],
        "data":{}
    }
}
```


The `data` sub-section allows you to provide HTML tags and attributes for areas of interest within
the defined section. This could be the title of a table or the heading of a section. Some of these `data` elements
allow AC to accurately parse the source HTML whereas others allow the user to parse further information from certain sections. 
Further details about the data elements can be found in [data_elements.md](data_elements.md) 



```
{
    "section":{
        "defined-by":[],
        "data":{
            "title":[
                {
                    "tag": "",
                    "attrs": ""
                }
            ]
        }
    }
}
```

Notice how the `data` sub-section is an object and the object entries are lists of objects
whereas `defined-by` is a list of objects.

When providing multiple objects in `defined-by` or within a `data` element there will be a logical OR
between the objects meaning that any sections or elements of interest within sections need only match
one of the provided `tag`/`attrs` pairs from any number provided.

Each `defined-by` or `data-element` list object can contain a `tag` and an `attrs` entry. The `tag` entry is where the HTML tag used to denote the section
can be provided. The `attrs` entry is used to pass in HTML attributes which can uniquely identify
this section from others. See below example

```
            {
                "tag": "div",
                "attrs": {"class": ["ref-cit-blk"]}
            }
```

The above example tells AC to look for all `<div>` tags with a class of "ref-cit-blk". "ref-cit-blk" is denoted as a JSON list,
this is optional and can be denoted as a single string instead but if a section would be uniquely identified by the use of two classes in combination, then both classes 
could be entered into the list. There is a logical AND operator applied to these values. 

You cannot state that a section is defined by the absence of a certain attribute or value.

Taking this further the value of the `tag` entry as well as all values within the `attrs` entry are processed as regex.
AC will automatically enclose any `tag` and `value` entries with the regex start (`^`) and end (`$`) anchors, this is to ensure there are no
erroneous matches. In config_pmc.json sub-sections are defined using the below `attrs`:

```
"attrs": {"class": "sec"}
```

Without the inclusion of the start and end anchors AC would also find matches to classes such as "tsec" and 
"sectionTitle", to ensure that all desired matches are found ensure that the value entered describes the whole of the 
`tag` or `attrs` value from the source html and not just part of it.

Below are two further examples of how this regex approach can be used:

```
            {
                "tag": "p",
                "attrs": {"id": "_{0,2}p\d+"}
            },
            {
                "tag": "h[3-6]"
            }
```

The first example looks for all `<p>` tags where the id looks something like `__p1` or `p12`. This is to allow for variability within how
the HTML is generated from each source without having to define exact matches for every possible format used.

The second example identifies all `header` elements ranging from `<h3>` to `<h6>`, AC will process all matching
headers at the same time.
