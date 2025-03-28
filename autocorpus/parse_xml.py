"""A script for running an XML parser version of Auto-CORPus.

This is still experimental and under development and is not part of the main too yet.

To use it run:

`python -m autocorpus.parse_xml <path_to_directory_containing_xml_files>`
"""

import glob
import json
import re
from datetime import datetime

import nltk
from bs4 import BeautifulSoup, NavigableString, ResultSet, Tag
from fuzzywuzzy import fuzz


def replace_spaces_and_newlines(input_string: str) -> str:
    """Replace multiple spaces and newline characters in a string with a single space.

    Args:
        input_string: The input string.

    Returns:
        The updated string.
    """
    # Replace multiple spaces (2 or more) with a single space
    input_string = re.sub(r" {2,}", " ", input_string)

    # Replace newline characters ('\n') with spaces
    input_string = input_string.replace("\n", " ")

    # Return the result
    return input_string


def _replace_match(match: re.Match) -> str:
    """Get the Unicode character corresponding to the escape sequence in a regex match.

    Args:
        match: The regular expression match object.
            Must contain a Unicode escape sequence.

    Returns:
        The unicode character corresponding to the escape sequence.
    """
    # Extract the Unicode escape sequence (e.g., \uXXXX)
    unicode_escape = match.group(0)

    # Decode the escape sequence to get the corresponding character
    unicode_char = bytes(unicode_escape, "utf-8").decode("unicode_escape")

    # Return the result
    return unicode_char


def replace_unicode_escape(input_string: str):
    """Find and replace unicode escape sequences with the actual characters in a string.

    Args:
        input_string: The input string containing Unicode escape sequences.

    Returns:
        The updated string with Unicode escape sequences replaced by actual characters.
    """
    # Use a regular expression to find all Unicode escape sequences (e.g., \uXXXX)
    pattern = re.compile(r"\\u[0-9a-fA-F]{4}")
    # Replace Unicode escape sequences with actual characters
    output_string = pattern.sub(_replace_match, input_string)

    # Return the result
    return output_string


def read_mapping_file() -> dict:
    """Read the IAO mapping file and create a dictionary of IAO terms and headings.

    Returns:
        A dictionary mapping IAO terms to their corresponding headings.
    """
    # Initialize an empty dictionary to store the mapping between IAO terms and headings
    mapping_dict: dict = {}

    # Open the mapping file in read mode
    with open("./data/IAO_FINAL_MAPPING.txt", encoding="utf-8") as f:
        # Read all lines from the file
        lines = f.readlines()

        # Iterate over each line in the file
        for line in lines:
            # Extract the heading (first column) and IAO term (second column) from the tab-separated line
            heading = line.split("\t")[0].lower().strip("\n")
            IAO_term = line.split("\t")[1].lower().strip("\n")

            # Check if the IAO term is not empty
            if IAO_term != "":
                # Handle cases where the IAO term contains multiple entries separated by a '/'
                if "/" in IAO_term:
                    # Split the IAO term into two parts
                    IAO_term_1 = IAO_term.split("/")[0].strip(" ")
                    IAO_term_2 = IAO_term.split("/")[1].strip(" ")

                    # Update the mapping dictionary for the first part of the IAO term
                    if IAO_term_1 in mapping_dict.keys():
                        mapping_dict[IAO_term_1].append(heading)
                    else:
                        mapping_dict.update({IAO_term_1: [heading]})

                    # Update the mapping dictionary for the second part of the IAO term
                    if IAO_term_2 in mapping_dict.keys():
                        mapping_dict[IAO_term_2].append(heading)
                    else:
                        mapping_dict.update({IAO_term_2: [heading]})

                # Handle cases where the IAO term does not contain '/'
                else:
                    # Update the mapping dictionary for the single IAO term
                    if IAO_term in mapping_dict.keys():
                        mapping_dict[IAO_term].append(heading)
                    else:
                        mapping_dict.update({IAO_term: [heading]})

    # Return the result
    return mapping_dict


def read_IAO_term_to_ID_file():
    """Read the IAO term to ID mapping file and create a dictionary of IAO terms and IDs.

    Returns:
        A dictionary mapping IAO terms to their corresponding IDs.
    """
    # Initialize an empty dictionary to store the mapping between IAO terms and their corresponding IDs
    IAO_term_to_no_dict = {}

    # Open the file containing the mapping between IAO terms and IDs
    with open("./data/IAO_term_to_ID.txt") as f:
        # Read all lines from the file
        lines = f.readlines()

        # Iterate over each line in the file
        for line in lines:
            # Extract the IAO term (first column) and the corresponding ID (second column)
            IAO_term = line.split("\t")[0]
            IAO_no = line.split("\t")[1].strip(
                "\n"
            )  # Remove any trailing newline characters from the ID

            # Update the dictionary with the IAO term as the key and the ID as the value
            IAO_term_to_no_dict.update({IAO_term: IAO_no})

    # Return the result
    return IAO_term_to_no_dict


def __add_IAO(section_heading, IAO_term):
    # Initialize a dictionary to store the paper's section heading and associated IAO term
    paper = {}

    # Assign the IAO term to the section heading in the paper dictionary
    paper.update({section_heading: IAO_term})

    # Retrieve the mapping dictionary of IAO terms to their IDs using the helper function
    IAO_term_to_no_dict = read_IAO_term_to_ID_file()

    # Check if the given IAO term exists in the dictionary
    if IAO_term in IAO_term_to_no_dict.keys():
        # If the term exists, get its corresponding ID
        mapping_result_ID_version = IAO_term_to_no_dict[IAO_term]
    else:
        # If the term does not exist, set the ID version to an empty string
        mapping_result_ID_version = ""

    # Return a dictionary containing the IAO term and its corresponding ID
    return {
        "iao_name": IAO_term,  # Name of the IAO term
        "iao_id": mapping_result_ID_version,  # ID associated with the IAO term, or empty if not found
    }


def extract_section_content(
    section: ResultSet,
    soup2: BeautifulSoup,
    ori_title: str,
):
    """Extract the content of a section and its subsections recursively.

    Args:
        section: A BeautifulSoup ResultSet object representing a section of the document.
        soup2: A BeautifulSoup object representing the entire document.
        ori_title: The original title of the section.
    """
    # Extract the current section's title, or use the original title if none is found
    curren_title = section.find("title")
    if curren_title is None:  # If no title is found, fall back to the original title
        curren_title = ori_title

    # If a title is available, attempt to locate it in the soup2 object
    if curren_title is not None:
        target_title = soup2.find(
            "title", string=f"{curren_title.text}"
        )  # Find the exact title in the soup2 object

        if target_title is not None:
            # Find the hierarchy of parent titles for the current title
            parent_titles = find_parent_titles(target_title)
        else:
            parent_titles = []

        # If there are multiple parent titles, exclude the last one (likely redundant)
        if len(parent_titles) > 1:
            parent_titles = parent_titles[:-1]
    else:
        parent_titles = None  # If no current title, set parent titles to None

    # Extract the content within the current section, specifically paragraphs (`<p>` tags)
    content = BeautifulSoup("<sec" + str(section).split("<sec")[1]).find_all("p")

    # If content is found, process each paragraph
    if content:
        for i in range(len(content)):
            # Avoid adding duplicate or null content
            if f"{content[i]}" not in text_list and content[i] is not None:
                # If no parent titles are found, tag the content with 'Unknown'
                if parent_titles is None:
                    tag_title.append(["Unknown"])
                else:
                    # Otherwise, tag it with the identified parent titles
                    tag_title.append(parent_titles)

                # Similarly, handle subtitle tagging
                if curren_title is None:
                    tag_subtitle.append("Unknown")
                else:
                    tag_subtitle.append(f"{[curren_title.text]}")

                # Add the processed content to the text list
                text_list.append(f"{content[i]}")

    # Recursively process any subsections within the current section
    subsections = section.find_all("sec")
    for subsection in subsections:
        extract_section_content(subsection, soup2, ori_title)


def find_parent_titles(title_element: Tag | NavigableString) -> list[str]:
    """Find the parent titles of a given title element in the document hierarchy.

    Args:
        title_element: A BeautifulSoup Tag or NavigableString object representing a
            title element.

    Returns:
        A list of parent titles in the document hierarchy.
    """
    # Initialize an empty list to store parent titles
    parent_titles: list[str] = []

    # Find the immediate parent <sec> element of the given title element
    parent = title_element.find_parent(["sec"])

    # Traverse up the hierarchy of <sec> elements
    while parent:
        # Look for a <title> within the current parent <sec>
        title = parent.find("title")
        if title:
            # If a title is found, add it to the beginning of the parent_titles list
            parent_titles.insert(0, title.text)

        # Move up to the next parent <sec> in the hierarchy
        parent = parent.find_parent(["sec"])

    # Return the list of parent titles, ordered from topmost to immediate parent
    return parent_titles


if __name__ == "__main__":
    import sys

    ######### INPUT #########

    ### A directory containing the path to the XML files to be processed, is a list of str
    try:
        dir_path = sys.argv[1]
    except IndexError:
        dir_path = "./xml_hackathon"
    all_files = glob.glob(f"{dir_path}/*.xml")
    # all_files = glob.glob('./xml_hackathon/*.xml')
    # all_files = all_files[:10]
    # all_files = ['./PMC_original/PMC10001121.xml']
    # all_files = ['./PMC_original/PMC5829769.xml']

    ######### END INPUT #########

    ### General comment, except for the actual text present in the body and extracted, as XML markup language is based on tag contained in < and > they conevrt < and > in the main text with string i.e. it is safe to remove anything contained between < and > if the text has not been replaced
    ### re.sub('<[^>]+>', '', str(soup.find('A_TAG'))) != 'None' - will not produce an error in case of empty paragraph - during postprocessing empty paragraph are removed
    ### Need to be convert as a function
    ### Need to take an input path and output path as parameters

    # Initialize a int value that will record the number of files that were not correctly processed by the code
    fail_processing = 0

    # Iterate over the input list to processed all the documents, 'xyz' is a int, for the 1st human argument of the list xyz = 0
    for xyz in range(len(all_files)):
        # Print the current document position currently in processing and the total number of documents to be process
        print(f"{(xyz + 1)} out of {len(all_files)}")

        # If there is a problem when processing the file, the variable fail_processing + 1, some XML file extension are HTML language, sometime the XML obtained has a different configuration that is currently not handle
        try:
            # Get the file path
            path = all_files[xyz]

            # Open the XML file located at the specified path
            with open(f"{path}") as xml_file:
                # Read the contents of the XML file into a string
                text = xml_file.read()

            # Parse the XML content using BeautifulSoup with the 'lxml' parser
            soup = BeautifulSoup(text, features="lxml")

            # Get the current date in the format 'YYYYMMDD'
            current_date = datetime.now().strftime("%Y%m%d")

            # Set the source method description for tracking
            source_method = "Auto-CORPus (XML)"

            # Assign the current date to the variable 'date'
            date = f"{current_date}"

            # Check if the text content, after replacing the any characters contained between < >, of the 'license-p' tag within the 'front' section is not 'None'
            if (
                re.sub("<[^>]+>", "", str(soup.find("front").find("license-p")))
                != "None"
            ):
                # Extract the content of the 'license-p' tag and remove all the characters between < and >
                license_xml = re.sub("<[^>]+>", "", str(soup.find("license-p")))

                # Replace Unicode escape sequences in the extracted license content with the helper function defines above
                license_xml = replace_unicode_escape(license_xml)

                # Remove excess spaces and newlines from the processed license content with the helper function defines above
                license_xml = replace_spaces_and_newlines(license_xml)
            else:
                # If the 'license-p' tag is not found or has no content, assign an empty string
                license_xml = ""

            # Check if an 'article-id' tag with the attribute 'pub-id-type' equal to 'pmid' exists in the soup
            ### no check for unicode or hexacode or XML tags
            if soup.find("article-id", {"pub-id-type": "pmid"}) is not None:
                # Extract the text content of the 'article-id' tag with 'pub-id-type' set to 'pmid'
                pmid_xml = soup.find("article-id", {"pub-id-type": "pmid"}).text
            else:
                # If the tag is not found, assign an empty string as the default value
                pmid_xml = ""

            # Check if an 'article-id' tag with the attribute 'pub-id-type' equal to 'pmcid' exists in the soup
            ### no check for unicode or hexacode or XML tags
            if soup.find("article-id", {"pub-id-type": "pmcid"}) is not None:
                # Extract the text content of the 'article-id' tag and prepend 'PMC' to it
                pmcid_xml = (
                    "PMC" + soup.find("article-id", {"pub-id-type": "pmcid"}).text
                )
                # Old PMC files does not include PMC when the new ones include PMC
                pmcid_xml = pmcid_xml.replace("PMCPMC", "PMC")

                # Construct the PMC article URL using the extracted PMCID
                pmc_link = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid_xml}/"
            else:
                # If the tag is not found, assign default empty strings for both variables
                pmcid_xml = ""
                pmc_link = ""

            # Check if an 'article-id' tag with the attribute 'pub-id-type' equal to 'doi' exists in the soup
            ### no check for unicode or hexacode or XML tags
            if soup.find("article-id", {"pub-id-type": "doi"}) is not None:
                # Extract the text content of the 'article-id' tag with 'pub-id-type' set to 'doi'
                doi_xml = soup.find("article-id", {"pub-id-type": "doi"}).text
            else:
                # If the tag is not found, assign an empty string to the 'doi_xml' variable
                doi_xml = ""

            # Check if the 'journal-title' tag exists within 'front', and if it contains valid text i.e. not none after removing the character present between < and > to remove XML tag from the content
            ### no check for unicode or hexacode
            if (
                re.sub("<[^>]+>", "", str(soup.find("front").find("journal-title")))
                != "None"
            ):
                # If valid text exists, remove XML tags and extract the content
                journal_xml = re.sub("<[^>]+>", "", str(soup.find("journal-title")))
            else:
                # If the tag is not found or contains no text, assign an empty string
                journal_xml = ""

            # Check if the 'subject' tag exists within 'article-categories', and if it contains valid text i.e. not none after removing the character present between < and > to remove XML tag from the content
            if (
                re.sub(
                    "<[^>]+>", "", str(soup.find("article-categories").find("subject"))
                )
                != "None"
            ):
                # If valid text exists, remove XML tags and extract the content
                pub_type_xml = re.sub("<[^>]+>", "", str(soup.find("subject")))
            else:
                # If the tag is not found or contains no text, assign an empty string
                pub_type_xml = ""

            # Check if the 'accepted' date is found within 'date', and if it contains a 'year' tag
            ### no check for unicode or hexacode or XML tags
            if soup.find("date", {"date-type": "accepted"}) is not None:
                if (
                    soup.find("date", {"date-type": "accepted"}).find("year")
                    is not None
                ):
                    # Extract the text content of the 'year' tag if found
                    year_xml = (
                        soup.find("date", {"date-type": "accepted"}).find("year").text
                    )
                else:
                    # If 'year' is missing, assign an empty string
                    year_xml = ""
            else:
                # If 'accepted' date is missing, assign an empty string
                year_xml = ""

            # Initialize variables to store the offset, text, and tag-related information
            offset = 0
            offset_list = []
            text_list = []
            tag_title = []
            tag_subtitle = []

            # Check if the 'article-title' tag exists and contains valid text i.e. not none after removing the character present between < and > to remove XML tag from the content
            if re.sub("<[^>]+>", "", str(soup.find("article-title"))) != "None":
                # If valid text exists, remove XML tags and append it to text_list
                # > and <, some other special character, are actually present in the title they would be converted to their 'human' form, unicode and hexacode is check later
                text_list.append(re.sub("<[^>]+>", "", str(soup.find("article-title"))))
                # Append corresponding titles for the tag
                tag_title.append(["document title"])
                tag_subtitle.append(["document title"])

            # Check if the 'kwd-group' (keyword) tag exists and contains valid text i.e. not none after removing the character present between < and > to remove XML tag from the content
            if re.sub("<[^>]+>", "", str(soup.find("kwd-group"))) != "None":
                # If valid text exists, append the entire 'kwd-group' tag to text_list, remove the title as we fix it to 'keywords'
                kwd_group = soup.find("kwd-group")
                if kwd_group.find("title"):
                    kwd_group.find("title").extract()
                text_list.append(kwd_group)
                # Append corresponding titles for the tag
                tag_title.append(["keywords"])
                tag_subtitle.append(["keywords"])
                # Clean up the text by removing <ital> and <bol> tags from the keyword, the element [0] of the list is supposed to be the title, then element [1] is the keyword
                # Conversion for special character is done later, unicode and hexacode check later
                ### ERROR if not title is found than there is no element [1] as this become element [0] instead of 1
                text_list[1] = re.sub(
                    "</ital[^>]+>", "", re.sub("<ital[^>]+>", "", str(text_list[1]))
                )
                text_list[1] = re.sub(
                    "</bol[^>]+>", "", re.sub("<bol[^>]+>", "", str(text_list[1]))
                )

                # Initialize a list to hold the cleaned keyword entries
                current = []
                # Split the cleaned text (removed tag) by commas and filter out empty strings (if the string was only a tag)
                for i in range(
                    len(re.sub("<[^>]+>", ",", str(text_list[1])).split(","))
                ):
                    if re.sub("<[^>]+>", ",", str(text_list[1])).split(",")[i] != "":
                        current.append(
                            re.sub("<[^>]+>", ",", str(text_list[1])).split(",")[i]
                        )
                    # Old PMC XMLs is text when new one is a list
                    current_filtered = []
                    for i in range(len(current)):
                        current[i] = current[i].replace(",", "")
                        if current[i] == "\n":
                            pass
                        elif current[i] == "\n\n":
                            pass
                        elif current[i] == "":
                            pass
                        elif current[i] == " ":
                            pass
                        else:
                            current_filtered.append(current[i])
                # Join the cleaned entries with commas and reassign them to text_list[1]
                text_list[1] = ", ".join(current_filtered)

            # Check if the 'abstract' tag exists and contains valid text (stripping XML tags if there any text left)
            # ALL ABSTRACT CODE: Special characters, i.e. < and >, are converted to human form and unicode and hexacode is replaced later
            if re.sub("<[^>]+>", "", str(soup.find("abstract"))) != "None":
                # If there is only one 'abstract' tag (often would be at the form of unstructured abstract)
                if len(soup.find_all("abstract")) == 1:
                    # Check if the 'abstract' tag contains any 'title' elements (if 1 unstructured otherwise might be structured)
                    if len(soup.find("abstract").find_all("title")) > 0:
                        # Iterate over each 'title' found in the 'abstract' tag (create the passages with different abstract heading i.e structuring the abstract)
                        for title in soup.find("abstract").find_all("title"):
                            title_text = title.text
                            p_tags = []

                            # Find all sibling 'p' (paragraph) tags following the title (merging the text with the same title)
                            next_sibling = title.find_next_sibling("p")
                            while (
                                next_sibling and next_sibling.name == "p"
                            ):  # Check for 'p' elements
                                p_tags.append(next_sibling)
                                next_sibling = next_sibling.find_next_sibling()  # Get next sibling until no more then None and leave the while loop

                            # Append the text of each 'p' tag to 'text_list' and assign titles/subtitles
                            for p_tag in p_tags:
                                tag_title.append(["Abstract"])
                                tag_subtitle.append(
                                    [title_text]
                                )  # Title text from the 'title' tag
                                text_list.append(
                                    p_tag.text
                                )  # Content of the 'p' tag (paragraph)

                    else:
                        # If no 'title' elements are found within the 'abstract', store the whole abstract text (100% unstructured abstract from publisher XML tags)
                        text_list.append(str(re.sub("<[^>]+>", "", str(soup.abstract))))
                        tag_title.append(["Abstract"])
                        tag_subtitle.append(["Abstract"])

                # If there are multiple 'abstract' tags (structured abstract from the XML markup)
                elif len(soup.find_all("abstract")) > 1:
                    # Iterate through all 'abstract' tags
                    for notes in soup.find_all("abstract"):
                        # Check if the 'abstract' tag contains any 'title' elements
                        if len(notes.find_all("title")) > 0:
                            # Iterate over each 'title' found in the 'abstract' tag
                            for title in notes.find_all("title"):
                                title_text = title.text
                                p_tags = []

                                # Find all sibling 'p' (paragraph) tags following the title (merging the text with the same title)
                                next_sibling = title.find_next_sibling("p")
                                while (
                                    next_sibling and next_sibling.name == "p"
                                ):  # Check for 'p' elements
                                    p_tags.append(next_sibling)
                                    next_sibling = next_sibling.find_next_sibling()  # Get next sibling until no more then None and leave the while loop

                                # Append the text of each 'p' tag to 'text_list' and assign titles/subtitles
                                for p_tag in p_tags:
                                    tag_title.append(["Abstract"])
                                    tag_subtitle.append(
                                        [title_text]
                                    )  # Title text from the 'title' tag
                                    text_list.append(
                                        p_tag.text
                                    )  # Content of the 'p' tag (paragraph)

                        else:
                            # If no 'title' elements are found, just append the whole 'abstract' text (becomes multiple pasages without structure)
                            text_list.append(notes)
                            tag_title.append(["Abstract"])
                            tag_subtitle.append(["Abstract"])

                else:
                    # If there is no abstract or it doesn't match any conditions, do nothing
                    pass

            # Create a second soup object to perform modification of its content without modify the original soup object where more information will be extracted later in the code
            soup2 = BeautifulSoup(text, features="lxml")

            tableswrap_to_remove = soup2.find_all("table-wrap")
            # Iterate through the tables present in the 'table-wrap' tag and remove them from the soup object regardless of where in the soup the tag is present
            for tablewrap in tableswrap_to_remove:
                tablewrap.extract()

            tables_to_remove = soup2.find_all("table")
            # Iterate through the tables present in the 'table' tag and remove them from the soup object regardless of where in the soup the tag is present
            for table in tables_to_remove:
                table.extract()

            tablewrapfoot_to_remove = soup2.find_all("table-wrap-foot")
            # Iterate through the table footnotes present in the 'table-wrap-foot' tag and remove them from the soup object regardless of where in the soup the tag is present
            for tablewrapfoot in tablewrapfoot_to_remove:
                tablewrapfoot.extract()

            captions_to_remove = soup2.find_all("caption")
            # Iterate through the captions present in the 'caption' tag and remove them from the soup object regardless of where in the soup the tag is present
            for caption in captions_to_remove:
                caption.extract()

            formula_to_remove = soup2.find_all("inline-formula")
            # Iterate through the formulas present in the 'inline-formula' tag and remove them from the soup object regardless of where in the soup the tag is present
            for formula in formula_to_remove:
                formula.extract()

            front_to_remove = soup2.find_all("front")
            # Iterate through the front part of the document where metadata is saved as soup2 is used to extract the body of text present in the 'front' tag and remove them from the soup object regardless of where in the soup the tag is present
            for front in front_to_remove:
                front.extract()

            back_to_remove = soup2.find_all("back")
            # Iterate through the back part of the document where metadata is saved as soup2 is used to extract the body of text present in the 'back' tag and remove them from the soup object regardless of where in the soup the tag is present
            for back in back_to_remove:
                back.extract()

            fig_to_remove = soup2.find_all("fig")
            # Iterate through the figures present in the 'fig' tag and remove them from the soup object regardless of where in the soup the tag is present
            for fig in fig_to_remove:
                fig.extract()

            graphic_to_remove = soup2.find_all("graphic")
            # Iterate through the graphic elements present in the 'graphic' tag and remove them from the soup object regardless of where in the soup the tag is present
            for graphic in graphic_to_remove:
                graphic.extract()

            inlinegraphic_to_remove = soup2.find_all("inline-graphic")
            # Iterate through the graphic elements made as a one-liner present in the 'inline-graphic' tag and remove them from the soup object regardless of where in the soup the tag is present
            for inlinegraphic in inlinegraphic_to_remove:
                inlinegraphic.extract()

            inlinesupplementarymaterial_to_remove = soup2.find_all(
                "inline-supplementary-material"
            )
            # Iterate through the supplementary material elements made as a one-liner present in the 'inline-supplementary-material' tag and remove them from the soup object regardless of where in the soup the tag is present
            for inlinesupplementarymaterial in inlinesupplementarymaterial_to_remove:
                inlinesupplementarymaterial.extract()

            media_to_remove = soup2.find_all("media")
            # Iterate through the media elements present in the 'media' tag and remove them from the soup object regardless of where in the soup the tag is present
            for media in media_to_remove:
                media.extract()

            texmath_to_remove = soup2.find_all("tex-math")
            # Iterate through the math equations present in the 'tex-math' tag and remove them from the soup object regardless of where in the soup the tag is present
            for texmath in texmath_to_remove:
                texmath.extract()

            # Find all <sec> elements in the soup2 object
            sec_elements = soup2.find_all("sec")

            # Define a regular expression pattern to match XML tags, as < and > are replace in the text with a str
            pattern = r"</[^>]+>"

            # Iterate through each <sec> element found in the soup2 object, i.e in the body as front and back part have been removed
            for a in range(len(sec_elements)):
                # Convert the <sec> element to a string for manipulation
                text_test = str(sec_elements[a])

                # Find all the closing tags in the current <sec> element (e.g., </p>, </sec>, </title>), looking for opening is more difficult because of id and extra information never present in the closing, the logic is that each opening as a closing
                matches = re.findall(pattern, text_test)

                # Remove duplicate closing tags and create a list of unique matches
                good_matches = list(dict.fromkeys(matches))

                # Remove unwanted tags such as </p>, </sec>, and </title> from the list of matches, we need to keep these tag for later parsing the document, this manipulation is done to remove xref, italic, bold, ... tags
                if "</p>" in good_matches:
                    good_matches.remove("</p>")
                if "</sec>" in good_matches:
                    good_matches.remove("</sec>")
                if "</title>" in good_matches:
                    good_matches.remove("</title>")

                # Iterate over the remaining tags to remove them from the soup2 object converted as a string
                for b in range(len(good_matches)):
                    current_tag_remove = good_matches[b]  # Get the tag to remove
                    # Create the corresponding opening tag pattern to match in the content
                    opening = f"<{current_tag_remove.split('</')[1][:-1]}[^>]*>"

                    # Remove both the opening and closing tags from the text
                    text_test = re.sub(opening, "", text_test)
                    text_test = re.sub(current_tag_remove, "", text_test)

                # After all unwanted tags are removed from the converted string, update the sec_elements list with the cleaned <sec> element by reconverting to string to a soup object
                sec_elements[a] = BeautifulSoup(text_test, features="lxml").find_all(
                    "sec"
                )[
                    0
                ]  # we keep the 0 element because we want the paragraph as a all not specific section since the parsing is taking place after

            # Iterate through each <sec> element in the sec_elements list - extarct the main text of the body, all the <sec> from the soup2 object
            # modification of the extracted content is performed later
            for sec in sec_elements:
                # Check if the current <sec> element does not have a parent <sec> element
                if not sec.find_parent("sec"):
                    # If the <sec> element does not have a parent <sec>, find its title
                    ori_title = sec.find("title")

                    # Call the function extract_section_content defined above, passing the <sec> element that is composed as a block paragraph containing one or more passages, the soup2 object, and the title of the main <sec> but the function will refine the title search
                    ### Current function is based on global variable, in the future we might want to pass the values as argument and unpack them again - will not provoke an error but could be improve
                    extract_section_content(sec, soup2, ori_title)

            # Check if the text inside the <ack> (acknowledgement) tag, back to the main soup object, is not 'None' after removing anything present between < and >
            # the special characters, unicode and hexacode are check later
            if re.sub("<[^>]+>", "", str(soup.find("ack"))) != "None":
                # If there is only one <ack> tag
                if len(soup.find_all("ack")) == 1:
                    # Loop through all <title> tags inside the first <ack> tag
                    for title in soup.find("back").find("ack").find_all("title"):
                        title_text = title.text  # Extract the title text

                        # Initialize an empty list to hold the <p> tags
                        p_tags = []
                        # Find the <p> tags that follow the title
                        next_sibling = title.find_next_sibling("p")

                        # Loop through all <p> tags that follow the title tag
                        while next_sibling and next_sibling.name == "p":
                            p_tags.append(next_sibling)  # Add the <p> tag to the list
                            next_sibling = next_sibling.find_next_sibling()  # Move to the next sibling until None and get out of the while

                        # Loop through the collected <p> tags and extract the text
                        for p_tag in p_tags:
                            # Append the title and subtitle (same as the title) to the respective lists
                            tag_title.append([title_text])
                            tag_subtitle.append([title_text])
                            # Append the text of the <p> tag to the text_list
                            text_list.append(p_tag.text)

                # If there are multiple <ack> tags
                elif len(soup.find_all("ack")) > 1:
                    # Loop through all <ack> tags in the document
                    for notes in soup.find_all("ack"):
                        # Loop through all <title> tags inside each <ack> tag
                        for title in notes.find_all("title"):
                            title_text = title.text  # Extract the title text

                            # Initialize an empty list to hold the <p> tags
                            p_tags = []
                            # Find the <p> tags that follow the title
                            next_sibling = title.find_next_sibling("p")

                            # Loop through all <p> tags that follow the title tag
                            while next_sibling and next_sibling.name == "p":
                                p_tags.append(
                                    next_sibling
                                )  # Add the <p> tag to the list
                                next_sibling = next_sibling.find_next_sibling()  # Move to the next sibling until None and get out of the while

                            # Loop through the collected <p> tags and extract the text
                            for p_tag in p_tags:
                                # Append the title and subtitle (same as the title) to the respective lists
                                tag_title.append([title_text])
                                tag_subtitle.append([title_text])
                                # Append the text of the <p> tag to the text_list
                                text_list.append(p_tag.text)
                else:
                    pass  # If no <ack> tag is found, do nothing

            # Check if the content inside the <funding-statement> tag, from the main soup object, is not 'None' after removing the text between < and >
            # the special characters, unicode and hexacode are check later
            if re.sub("<[^>]+>", "", str(soup.find("funding-statement"))) != "None":
                # If there are any <title> tags inside the <funding-statement> tag
                if len(soup.find("funding-statement").find_all("title")) != 0:
                    # Loop through all the <title> tags inside <funding-statement>
                    for title in soup.find("funding-statement").find_all("title"):
                        title_text = title.text  # Extract the title text

                        # Initialize an empty list to hold the <p> tags
                        p_tags = []
                        # Find the <p> tags that follow the title
                        next_sibling = title.find_next_sibling("p")

                        # Loop through all <p> tags that follow the title tag
                        while next_sibling and next_sibling.name == "p":
                            p_tags.append(next_sibling)  # Add the <p> tag to the list
                            next_sibling = next_sibling.find_next_sibling()  # Move to the next sibling until None and get out of the while

                        # Loop through the collected <p> tags and extract the text
                        for p_tag in p_tags:
                            # Append the title and subtitle (same as the title) to the respective lists
                            tag_title.append([title_text])
                            tag_subtitle.append([title_text])
                            # Append the text of the <p> tag to the text_list
                            text_list.append(p_tag.text)

                # If there are no <title> tags but the <funding-statement> tag exists and is not 'None'
                elif (
                    re.sub("<[^>]+>", "", str(soup.find("funding-statement"))) != "None"
                ):
                    # Append 'Funding Statement' as both the title and subtitle to the lists
                    tag_title.append(["Funding Statement"])
                    tag_subtitle.append(["Funding Statement"])
                    # Append the content inside the <funding-statement> tag (without XML tags) to text_list
                    text_list.append(
                        re.sub("<[^>]+>", "", str(soup.find("funding-statement")))
                    )
                else:
                    pass  # If no <funding-statement> tag exists, do nothing

            # Check if the content inside the <fn-group> tag (footnotes), from the main soup object, is not 'None' after removing XML tags
            # the special characters, unicode and hexacode are check later
            if re.sub("<[^>]+>", "", str(soup.find("fn-group"))) != "None":
                # If there are any <title> tags inside the <fn-group> tag
                if len(soup.find("fn-group").find_all("title")) != 0:
                    # Loop through all the <title> tags inside <fn-group>
                    for title in soup.find("fn-group").find_all("title"):
                        title_text = title.text  # Extract the title text

                        # Initialize an empty list to hold the <p> tags
                        p_tags = []
                        # Find the <p> tags that follow the title
                        next_sibling = title.find_next_sibling("p")

                        # Loop through all <p> tags that follow the title tag
                        while next_sibling and next_sibling.name == "p":
                            p_tags.append(next_sibling)  # Add the <p> tag to the list
                            next_sibling = next_sibling.find_next_sibling()  # Move to the next sibling until None and get out of the while

                        # Loop through the collected <p> tags and extract the text
                        for p_tag in p_tags:
                            # Append the title and subtitle (same as the title) to the respective lists
                            tag_title.append([title_text])
                            tag_subtitle.append([title_text])
                            # Append the text of the <p> tag to the text_list
                            text_list.append(p_tag.text)

                # If there are no <title> tags but the <fn-group> tag exists and is not 'None'
                elif re.sub("<[^>]+>", "", str(soup.find("fn-group"))) != "None":
                    # Append 'Footnotes' as both the title and subtitle to the lists
                    tag_title.append(["Footnotes"])
                    tag_subtitle.append(["Footnotes"])
                    # Append the content inside the <fn-group> tag (without XML tags) to text_list
                    text_list.append(re.sub("<[^>]+>", "", str(soup.find("fn-group"))))
                else:
                    pass  # If no <fn-group> tag exists, do nothing

            # Check if the content inside the <app-group> tag is not 'None' after removing the XML tags
            # the special characters, unicode and hexacode are check later
            if re.sub("<[^>]+>", "", str(soup.find("app-group"))) != "None":
                # If there are any <title> tags inside the <app-group> tag
                if len(soup.find("app-group").find_all("title")) != 0:
                    # Loop through all the <title> tags inside <app-group>
                    for title in soup.find("back").find("app-group").find_all("title"):
                        title_text = title.text  # Extract the title text

                        # Initialize an empty list to hold the <p> tags
                        p_tags = []
                        # Find the <p> tags that follow the title
                        next_sibling = title.find_next_sibling("p")

                        # Loop through all <p> tags that follow the title tag
                        while next_sibling and next_sibling.name == "p":
                            p_tags.append(next_sibling)  # Add the <p> tag to the list
                            next_sibling = next_sibling.find_next_sibling()  # Move to the next sibling until None and get out of the while

                        # Loop through the collected <p> tags and extract the text
                        for p_tag in p_tags:
                            # Append the title and subtitle (same as the title) to the respective lists
                            tag_title.append([title_text])
                            tag_subtitle.append([title_text])
                            # Append the text of the <p> tag to the text_list
                            text_list.append(p_tag.text)

                # If there are no <title> tags but the <app-group> tag exists and is not 'None'
                elif re.sub("<[^>]+>", "", str(soup.find("app-group"))) != "None":
                    # Append 'Unknown' as both the title and subtitle to the lists
                    tag_title.append(["Unknown"])
                    tag_subtitle.append(["Unknown"])
                    # Append the content inside the <app-group> tag (without XML tags) to text_list
                    text_list.append(re.sub("<[^>]+>", "", str(soup.find("app-group"))))
                else:
                    pass  # If no <app-group> tag exists, do nothing

            # Check if the content inside the <notes> tag is not 'None' after removing XML tags
            if re.sub("<[^>]+>", "", str(soup.find("notes"))) != "None":
                # If there is only one <notes> tag
                if len(soup.find_all("notes")) == 1:
                    # Loop through all the <title> tags inside <notes>
                    ### ERROR make the code in case there is no title
                    for title in soup.find("notes").find_all("title"):
                        title_text = title.text  # Extract the title text

                        # Initialize an empty list to hold the <p> tags
                        p_tags = []
                        # Find the <p> tags that follow the title
                        next_sibling = title.find_next_sibling("p")

                        # Loop through all <p> tags that follow the title tag
                        while next_sibling and next_sibling.name == "p":
                            p_tags.append(next_sibling)  # Add the <p> tag to the list
                            next_sibling = next_sibling.find_next_sibling()  # Move to the next sibling until None and get out of the while

                        # Loop through the collected <p> tags and extract the text
                        for p_tag in p_tags:
                            # Append the title and subtitle (same as the title) to the respective lists
                            tag_title.append([title_text])
                            tag_subtitle.append([title_text])
                            # Append the text of the <p> tag to the text_list
                            text_list.append(p_tag.text)

                # If there are multiple <notes> tags
                elif len(soup.find_all("notes")) > 1:
                    # Loop through each <notes> tag
                    for notes in soup.find_all("notes"):
                        # Loop through all the <title> tags inside the current <notes> tag
                        ### ERROR make the code in case there is no title
                        for title in notes.find_all("title"):
                            title_text = title.text  # Extract the title text

                            # Initialize an empty list to hold the <p> tags
                            p_tags = []
                            # Find the <p> tags that follow the title
                            next_sibling = title.find_next_sibling("p")

                            # Loop through all <p> tags that follow the title tag
                            while next_sibling and next_sibling.name == "p":
                                p_tags.append(
                                    next_sibling
                                )  # Add the <p> tag to the list
                                next_sibling = next_sibling.find_next_sibling()  # Move to the next sibling until None and get out of the while

                            # Loop through the collected <p> tags and extract the text
                            for p_tag in p_tags:
                                # Append the title and subtitle (same as the title) to the respective lists
                                tag_title.append([title_text])
                                tag_subtitle.append([title_text])
                                # Append the text of the <p> tag to the text_list
                                text_list.append(p_tag.text)
                else:
                    pass  # If no <notes> tag exists, do nothing

            # Initialize lists to store the reference data
            tag_title_ref = []
            tag_subtitle_ref = []
            text_list_ref = []
            source_list = []
            year_list = []
            volume_list = []
            doi_list = []
            pmid_list = []

            # Find all <ref> tags in the main soup object as present in the <back> tag
            ref_tags = soup.find_all("ref")

            # Loop through each <ref> tag to extract citation information
            for ref in ref_tags:
                # Check if the <ref> tag contains an 'element-citation' tag with a publication type of 'journal', we can parse this format one when the other citation formats will not be parsed
                if (
                    ref.find("element-citation", {"publication-type": "journal"})
                    is not None
                ):
                    # Extract the label, which may or may not exist
                    label = ref.label.text if ref.label else ""

                    # Extract the article title, which may or may not exist
                    article_title = (
                        ref.find("article-title").text
                        if ref.find("article-title")
                        else ""
                    )

                    # Extract the source (journal name), which may or may not exist
                    source = ref.source.text if ref.source else ""

                    # Extract the year of publication, which may or may not exist
                    year = ref.year.text if ref.year else ""

                    # Extract the volume of the publication, which may or may not exist
                    volume = ref.volume.text if ref.volume else ""

                    # Extract the DOI, if available
                    doi = (
                        ref.find("pub-id", {"pub-id-type": "doi"}).text
                        if ref.find("pub-id", {"pub-id-type": "doi"})
                        else ""
                    )

                    # Extract the PMID, if available
                    pmid = (
                        ref.find("pub-id", {"pub-id-type": "pmid"}).text
                        if ref.find("pub-id", {"pub-id-type": "pmid"})
                        else ""
                    )

                    # Initialize an empty list to store the authors
                    authors = []

                    # Check if there is a <person-group> tag for authors
                    if (
                        ref.find("person-group", {"person-group-type": "author"})
                        is not None
                    ):
                        author_group = ref.find(
                            "person-group", {"person-group-type": "author"}
                        )

                        # Loop through all <name> tags in the author group
                        if len(author_group.find_all("name")) > 0:
                            for name in author_group.find_all("name"):
                                surname = (
                                    name.surname.text
                                )  # Extract the surname of the author
                                given_names = (
                                    name.find("given-names").text
                                    if name.find("given-names")
                                    else ""
                                )  # Extract given names, if available
                                authors.append(
                                    f"{given_names} {surname}"
                                )  # Append the author's name to the authors list

                    # Check for the presence of <etal> (et al.)
                    etal_tag = ref.find("etal")
                    if etal_tag is not None:
                        etal = "Et al."  # Add "Et al." if the tag is present
                    else:
                        etal = ""

                    # If 'etal' is found, append it to the final authors list
                    ### ERROR authors could be an empty list, need to figure out if the above tag is absent what to do
                    if etal != "":
                        final_authors = f"{', '.join(authors)} {etal}"
                    else:
                        final_authors = f"{', '.join(authors)}"

                    # Append the reference data to the lists
                    tag_title_ref.append(["References"])
                    tag_subtitle_ref.append(["References"])
                    ### Not checked for XML tags, special characters not converted to human readable format
                    # unicode and hexa checked later
                    ### might need to look at the conditional of this one again
                    text_list_ref.append(
                        f"{label}{' ' + final_authors if final_authors else ''}{', ' + article_title if article_title else ''}{', ' + source if source else ''}{', ' + year if year else ''}{';' + volume if volume and year else ''}{', ' + volume if volume and not year else ''}"
                    )

                    # Append additional citation details to the respective lists
                    source_list.append(source)
                    year_list.append(year)
                    volume_list.append(volume)
                    doi_list.append(doi)
                    pmid_list.append(pmid)

                else:
                    # If the <ref> tag does not contain an 'element-citation' tag, extract the text content as-is
                    content = ref.get_text(separator=" ")

                    # Append the content to the reference lists
                    tag_title_ref.append(["References"])
                    tag_subtitle_ref.append(["References"])

                    ### Not checked for XML tags, special characters not converted to human readable format
                    # unicode and hexa checked later
                    text_list_ref.append(content)

                    # can't be parsed because we don't know the formats used
                    source_list.append("")
                    year_list.append("")
                    volume_list.append("")
                    doi_list.append("")
                    pmid_list.append("")

            # Iterate through each element in the 'tag_title' list from the <front>, <abstract>, all the extracted text from soup2 object, and some information from the <back> outside of references saved in a different list
            for i in range(len(tag_title)):
                # Clean 'tag_subtitle[i]' by removing XML tags and unwanted characters, this is the most recent heading for the text
                # Remove all XML tags using regex
                # Remove single quotes from the string, removing the list syntax from the string
                # Remove opening square brackets from the string, removing the list syntax from the string
                # Remove closing square brackets from the string, removing the list syntax from the string
                # Remove double quotes from the string, removing the list syntax from the string
                tag_subtitle[i] = [
                    re.sub("<[^>]+>", "", str(tag_subtitle[i]))
                    .replace("'", "")
                    .replace("[", "")
                    .replace("]", "")
                    .replace('"', "")
                ]

                # Iterate through each sublist in 'tag_title[i]'
                for j in range(len(tag_title[i])):
                    # Clean each element (title) in the sublist by removing XML tags and unwanted characters, this is all the parent headings for the text
                    # Remove all XML tags using regex
                    # Remove single quotes from the string, removing the list syntax from the string
                    # Remove opening square brackets from the string, removing the list syntax from the string
                    # Remove closing square brackets from the string, removing the list syntax from the string
                    # Remove double quotes from the string, removing the list syntax from the string
                    tag_title[i][j] = [
                        re.sub("<[^>]+>", "", str(tag_title[i][j]))
                        .replace("'", "")
                        .replace("[", "")
                        .replace("]", "")
                        .replace('"', "")
                    ]

            # Iterate through each element in the 'tag_title' list
            for i in range(len(tag_title)):
                # Iterate through each sublist in 'tag_title[i]'
                for j in range(len(tag_title[i])):
                    # Check if the string in the first element of the current sublist has more than one word, i.e. a space is present
                    if len(tag_title[i][j][0].split()) > 1:
                        # Check if the first word ends with a period
                        if tag_title[i][j][0].split()[0][-1] == ".":
                            # Check if the first word (excluding the period) is a number (ignoring commas and periods)
                            if (
                                tag_title[i][j][0]
                                .split()[0][:-1]
                                .replace(".", "")
                                .replace(",", "")
                                .isdigit()
                            ):
                                # Remove the first word (likely a number followed by a period) and join the remaining words
                                tag_title[i][j][0] = " ".join(
                                    tag_title[i][j][0].split()[1:]
                                )

            # Iterate through each element in the 'tag_subtitle' list
            for i in range(len(tag_subtitle)):
                # Check if the first element in the current sublist contains more than one word
                if len(tag_subtitle[i][0].split()) > 1:
                    # Check if the first word ends with a period
                    if tag_subtitle[i][0].split()[0][-1] == ".":
                        # Check if the first word (excluding the period) is a number (ignoring commas and periods)
                        if (
                            tag_subtitle[i][0]
                            .split()[0][:-1]
                            .replace(".", "")
                            .replace(",", "")
                            .isdigit()
                        ):
                            # Remove the first word (likely a number followed by a period) and join the remaining words
                            tag_subtitle[i][0] = " ".join(
                                tag_subtitle[i][0].split()[1:]
                            )

            # Iterate over all elements in 'text_list'
            for i in range(len(text_list)):
                # Remove anything from '<sec[^*]' until '/title>' str and '</sec>' str from each element of text_list
                text_list[i] = re.sub(
                    "<sec[^*]+/title>", "", str(text_list[i])
                ).replace("</sec>", "")

            # Iterate over all elements in 'text_list'
            for i in range(len(text_list)):
                # Replace Unicode escape sequences with actual characters, from the function introduced above
                text_list[i] = replace_unicode_escape(text_list[i])

            # Iterate over all elements in 'text_list'
            for i in range(len(text_list)):
                # Replace multiple spaces and newlines in the text with single spaces, from the function introduced above
                text_list[i] = replace_spaces_and_newlines(text_list[i])

            # Define a pattern to match <xref> tags in the text (reference cross-references)
            ### in my opinion not in used anymore as all the tags except sec title and p are kept in soup2 object
            pattern = r"(<xref[^>]*>)([^<]+)(</xref>)"

            # Iterate over all elements in 'text_list'
            for i in range(len(text_list)):
                # Apply regex pattern to reformat <xref> tags by adding a space between the tag content
                ### in my opinion not in used anymore as all the tags except sec title and p are kept in soup2 object
                text_list[i] = re.sub(pattern, r"\1 \2 \3", text_list[i])

            # Iterate over all elements in 'text_list' again
            for i in range(len(text_list)):
                # Replace spaces and newlines in the text once more after the <xref> tags are modified, from the function introduced above
                ### in my opinion not in used anymore as all the tags except sec title and p are kept in soup2 object
                text_list[i] = replace_spaces_and_newlines(text_list[i])

            # Initialize empty lists to store corrected sections, subsections, text, and offsets
            corrected_section = []
            corrected_subsection = []
            corrected_text = []

            # Iterate over each element in the 'text_list'
            for i in range(len(text_list)):
                # Check if the current element in text_list is not empty
                if text_list[i] != "":
                    # Iterate over each section split by <p> tags in the current text
                    for j in range(len(text_list[i].split("<p>"))):
                        # Check if the current section (split by <p>) is not empty after removing </p> tags
                        if text_list[i].split("<p>")[j].replace("</p>", "") != "":
                            # Append the corresponding tag title and tag subtitle for the section
                            corrected_section.append(tag_title[i])
                            corrected_subsection.append(tag_subtitle[i])

                            # Remove all tags from the current p text from the current item of the text_list
                            new_text = str(
                                re.sub("<[^>]+>", "", str(text_list[i].split("<p>")[j]))
                            )
                            # Replace unicode and hexacode, using the function introduced above
                            new_text = replace_unicode_escape(new_text)
                            # Replace spaces and newlines, using the function introduced above
                            new_text = replace_spaces_and_newlines(new_text)
                            # Clean up special characters
                            # Replace </p> with an empty string (### not sure it's necessary anymore) and handle XML entities like <, >, &, ', and "
                            new_text = (
                                new_text.replace("</p>", "")
                                .replace("&lt;", "<")
                                .replace("&gt;", ">")
                                .replace("&amp;", "&")
                                .replace("&apos;", "'")
                                .replace("&quot;", '"')
                            )

                            # Append the corrected text to the corrected_text list
                            corrected_text.append(new_text)

                            # Update the offset list (keeps track of the position in the document)
                            offset_list.append(offset)

                            # Increment the offset by the length of the new text + 1 (for spacing or next content)
                            offset += len(new_text) + 1
                        else:
                            # If the current section is empty after removing </p>, skip it
                            pass
                else:
                    # If the current text list element is empty, skip it
                    pass

            # Correct any missing section titles by copying the previous title if the current title is empty
            for i in range(len(corrected_section)):
                if len(corrected_section[i]) == 0:
                    corrected_section[i] = corrected_section[i - 1]

            ### No XML tags remove here or special characters conversion
            # Initialize an empty list to store offsets for references
            offset_list_ref = []

            # Iterate over each element in the 'text_list_ref' (list containing reference texts)
            for i in range(len(text_list_ref)):
                # Replace unicode and hexacode, using the function introduced above
                text_list_ref[i] = replace_unicode_escape(text_list_ref[i])

            # Iterate over each element in the 'text_list_ref' (list containing reference texts)
            for i in range(len(text_list_ref)):
                # Replace spaces and newlines, using the function introduced above
                text_list_ref[i] = replace_spaces_and_newlines(text_list_ref[i])

            # Iterate over each element in the 'text_list_ref' to calculate and store offsets
            for i in range(len(text_list_ref)):
                # Append the current value of 'offset' to the offset list for the reference
                offset_list_ref.append(offset)

                # Update the 'offset', as it comes after the main text by adding the length of the current reference text + 1, the +1 accounts for a space or delimiter between references
                offset += len(text_list_ref[i]) + 1

            ######### FROM AC MAIN LIBRARY #########

            mapping_dict = read_mapping_file()

            # Main body IAO allocation
            iao_list = []

            for y in range(len(corrected_section)):
                if corrected_section[y][0][0] == "document title":
                    section_type = [
                        {"iao_name": "document title", "iao_id": "IAO:0000305"}
                    ]
                else:
                    tokenized_section_heading = nltk.wordpunct_tokenize(
                        corrected_section[y][0][0]
                    )
                    text = nltk.Text(tokenized_section_heading)
                    words = [w.lower() for w in text]
                    h2_tmp = " ".join(word for word in words)

                    # TODO: check for best match, not the first
                    if h2_tmp != "":
                        if any(x in h2_tmp for x in [" and ", "&", "/"]):
                            mapping_result = []
                            h2_parts = re.split(r" and |\s?/\s?|\s?&\s?", h2_tmp)
                            for h2_part in h2_parts:
                                h2_part = re.sub(r"^\d*\s?[\(\.]]?\s?", "", h2_part)
                                pass
                                for IAO_term, heading_list in mapping_dict.items():
                                    for i in range(len(heading_list)):
                                        if fuzz.ratio(h2_part, heading_list[i]) > 80:
                                            mapping_result.append(
                                                __add_IAO(heading_list[i], IAO_term)
                                            )

                        else:
                            mapping_result = []
                            for IAO_term, heading_list in mapping_dict.items():
                                h2_tmp = re.sub(r"^\d*\s?[\(\.]]?\s?", "", h2_tmp)
                                for i in range(len(heading_list)):
                                    if fuzz.ratio(h2_tmp, heading_list[i]) > 80:
                                        mapping_result.append(
                                            __add_IAO(heading_list[i], IAO_term)
                                        )
                    else:
                        mapping_result = []

                    # if condition to add the default value 'document part' for passages without IAO
                    if mapping_result == []:
                        section_type = [
                            {
                                "iao_name": "document part",  # Name of the IAO term
                                "iao_id": "IAO:0000314",  # ID associated with the IAO term, or empty if not found
                            }
                        ]
                    else:
                        section_type = mapping_result

                iao_list.append(list({v["iao_id"]: v for v in section_type}.values()))

            # References IAO allocation
            iao_list_ref = []

            for y in range(len(tag_title_ref)):
                section_type = [
                    {
                        "iao_name": "References",  # Name of the IAO term
                        "iao_id": "IAO:0000320",  # ID associated with the IAO term, or empty if not found
                    }
                ]

                iao_list_ref.append(
                    list({v["iao_id"]: v for v in section_type}.values())
                )

            ######### END AC MAIN LIBRARY #########

            # Initialize lists to store embedded data
            embeded_list = []  # Final list containing all embedded documents
            embeded_section_list = []  # Final list containing all the infons information, excluding reference
            embeded_section_ref_list = []  # Final list containing all the infons for the reference section

            # Loop through corrected_section to create embedded section dictionaries
            for i in range(len(corrected_section)):
                # Create a dictionary for the first-level section title
                embeded_dict = {
                    "section_title_1": corrected_section[i][0][0]  # First section title
                }
                cont_section = 2  # Counter for additional section titles

                # If there are more levels in the section, add them to the dictionary, i.e. subheadings
                if len(corrected_section[i]) > 1:
                    for imp in range(1, len(corrected_section[i])):
                        embeded_dict[f"section_title_{cont_section}"] = (
                            corrected_section[i][imp][0]
                        )
                        cont_section += 1

                # If the subsection is different from the main section, add it as well i.e. the last subheading if there is a main heading
                if corrected_subsection[i][0] != corrected_section[i][0][0]:
                    embeded_dict[f"section_title_{cont_section}"] = (
                        corrected_subsection[i][0]
                    )

                # Add IAO data (if available) to the dictionary
                if len(iao_list[i]) > 0:
                    for y in range(len(iao_list[i])):
                        embeded_dict[f"iao_name_{y}"] = iao_list[i][y].get("iao_name")
                        embeded_dict[f"iao_id_{y}"] = iao_list[i][y].get("iao_id")

                # Append the completed dictionary to the embedded section list
                embeded_section_list.append(embeded_dict)

            # Process reference sections (tag_title_ref) to create embedded reference dictionaries
            for i in range(len(tag_title_ref)):
                embeded_dict = {
                    "section_title_1": tag_title_ref[i][
                        0
                    ]  # First section title i.e. 'Reference'
                }

                # Add IAO data (if available) for references
                if len(iao_list_ref[i]) > 0:
                    for y in range(len(iao_list_ref[i])):
                        embeded_dict[f"iao_name_{y}"] = iao_list_ref[i][y].get(
                            "iao_name"
                        )
                        embeded_dict[f"iao_id_{y}"] = iao_list_ref[i][y].get("iao_id")

                # Add metadata from references if available
                if source_list[i] != "":
                    embeded_dict["journal"] = source_list[i]
                if year_list[i] != "":
                    embeded_dict["year"] = year_list[i]
                if volume_list[i] != "":
                    embeded_dict["volume"] = volume_list[i]
                if doi_list[i] != "":
                    embeded_dict["doi"] = doi_list[i]
                if pmid_list[i] != "":
                    embeded_dict["pmid"] = pmid_list[i]

                # Append the completed dictionary to the embedded section reference list
                embeded_section_ref_list.append(embeded_dict)

            # Combine corrected text with embedded sections into final embedded list
            for i in range(len(corrected_text)):
                # If after cleaning the there is no more text or only a space, we don't keep them
                if corrected_text[i] == "" or corrected_text[i] == " ":
                    pass
                else:
                    embeded_dict = {
                        "offset": offset_list[i],  # Offset for the text
                        "infons": embeded_section_list[i],  # Section metadata
                        "text": corrected_text[i],  # Main text
                        "sentences": [],  # Placeholder for sentences
                        "annotations": [],  # Placeholder for annotations
                        "relations": [],  # Placeholder for relations
                    }
                    # Populate the list of passages
                    embeded_list.append(embeded_dict)

            # Add reference text with metadata to the embedded list
            for i in range(len(text_list_ref)):
                # If after cleaning the there is no more text or only a space, we don't keep them
                if text_list_ref[i] == "" or text_list_ref[i] == " ":
                    pass
                else:
                    embeded_dict = {
                        "offset": offset_list_ref[i],  # Offset for reference text
                        "infons": embeded_section_ref_list[i],  # Reference metadata
                        "text": text_list_ref[i],  # Reference text
                        "sentences": [],  # Placeholder for sentences
                        "annotations": [],  # Placeholder for annotations
                        "relations": [],  # Placeholder for relations
                    }
                    # Populate the list of passages
                    embeded_list.append(embeded_dict)

            # Create a dictionary for document metadata
            infons_dict_meta = {}
            if pmcid_xml != "":
                infons_dict_meta["pmcid"] = pmcid_xml
            if pmid_xml != "":
                infons_dict_meta["pmid"] = pmid_xml
            if doi_xml != "":
                infons_dict_meta["doi"] = doi_xml
            if pmc_link != "":
                infons_dict_meta["link"] = pmc_link
            if journal_xml != "":
                infons_dict_meta["journal"] = journal_xml
            if pub_type_xml != "":
                infons_dict_meta["pub_type"] = pub_type_xml
            if year_xml != "":
                infons_dict_meta["year"] = year_xml
            if license_xml != "":
                infons_dict_meta["license"] = license_xml

            # Create the final dictionary for the document
            my_dict = {}
            if source_method != "":
                my_dict["source"] = source_method
            if date != "":
                my_dict["date"] = date
            my_dict["key"] = "autocorpus_fulltext.key"
            my_dict["infons"] = infons_dict_meta  # Metadata for the document
            my_dict["documents"] = [
                {
                    "id": pmcid_xml,  # Document ID
                    "infons": {},  # Placeholder for additional document-level infons
                    "passages": embeded_list,  # Embedded passages including sections and references
                    "relations": [],  # Placeholder for relations at the document level
                }
            ]

            ######### OUTPUT #########

            with open(
                f"./xml_hackathon/{all_files[xyz].split('/')[-1].split('.')[0]}.json",
                "w",
                encoding="utf-8",
            ) as fp:
                json.dump(my_dict, fp, indent=2, ensure_ascii=False)

            ######### END OUTPUT #########

        # If the code above, runs into an error then we handle the error by skipping the current document to be processed and increment the variable 'fail_processing' +1 if the document is not recognised as an HTML
        except Exception:
            # Get the file path for the current XML file from the list of all files
            path = all_files[xyz]

            # Open the XML file located at the specified path for reading
            with open(f"{path}") as xml_file:
                # Read the entire contents of the file into the variable 'text'
                text = xml_file.read()

            # Parse the XML content using BeautifulSoup with the 'lxml' parser
            soup = BeautifulSoup(text, features="lxml")

            # Check if the parsed content contains an HTML structure (by examining the first 10 characters of the string of the BeautifulSoup object)
            if "html" in str(soup)[:10]:
                # If the content starts with or contains 'html', do not increment the variable 'fail_processing' as this code is for XML and not HTML
                pass
            else:
                # If the content does not appear to be HTML, increment the failure counter
                fail_processing += 1

    # Print the number of documents that couldn't be processed by the above code
    print(fail_processing)
