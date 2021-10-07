**How to create/edit a config file**

We will use config_pmc.json as the example config for this guide.

There are no required sections within the config file, if you do not define a section then Auto-CORPus will not try to process it.
Auto-CORPus will also not try to process any sections defined within the configs which are not within our template config file, 
so we recommend starting from the template config file or a working config file and modify from there.

For each section in a publication, the config declares `data` and `defined-by` entities. 

```
{
    "section":{
        "defined-by":[],
        "data":{}
    }
}
```

The `defined-by` entity provides a list of HTML tags and attributes which Auto-CORPus can utilise to find ocurrences of the 
section within the source HTML. Each section must contain a `defined-by` entity.

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

The `data` entity allows HTML tags and attributes for areas of interest within
the defined section to be defined. This could be the title of a table or the heading of a section. Some of these `data` elements
allow Auto-CORPus to accurately parse the source HTML whereas others allow the user to parse further information from certain sections. 
The `data` entity is optional and further details about the `data` elements can be found in [data_elements.md](data_elements.md).
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
The `data` entity is an object and the object entries are lists of objects
whereas `defined-by` is a list of objects.

When providing multiple objects in `defined-by` or within a `data` element there will be a logical OR
between the objects meaning that the source HTML need only match
one of the provided `tag`/`attrs` pairs.

Each `defined-by` or `data` element list object can contain a `tag` and an `attrs` entry. The `tag` entry defines the HTML tag used to denote the section. The `attrs` entry is used to pass in HTML attributes which can uniquely identify
this section from others.

```
            {
                "tag": "div",
                "attrs": {"class": ["ref-cit-blk"]}
            }
```

The above example tells Auto-CORPus to look for all `<div>` tags with a class of "ref-cit-blk". "ref-cit-blk" is denoted as a JSON list.  The use of a list allows other classes to be defined, that when used in combination, uniquly identify a section.  Hence, the logical AND operator is applied to these values. 

Regular expressions can be used within the `tag` entry value and `attrs` entry values.
Auto-CORPus will automatically enclose any `tag` and `value` entries with the regex start (`^`) and end (`$`) anchors, this is to ensure there are no
erroneous matches. In config_pmc.json, entities are defined using the below `attrs`:

```
"attrs": {"class": "sec"}
```

Without the inclusion of the start and end anchors, Auto-CORPus would also find matches to classes such as "tsec" and 
"sectionTitle".  To ensure that all desired matches are found, ensure that the value entered describes the whole of the 
`tag` or `attrs` value from the source HTML and not just part of it.

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

The second example identifies all `header` elements ranging from `<h3>` to `<h6>`. Auto-CORPus will process all matching
headers at the same time.
