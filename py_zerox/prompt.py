# conversion_config.py

INPUT_FORMAT = "PDF"
TARGET_FORMAT = "Latex"

SYSTEM_ROLE = """You are an expert system that converts {in_format} files to {tgt_format}""".format(
    in_format=INPUT_FORMAT, tgt_format=TARGET_FORMAT
)

INPUT_STRUCTURE = """
- File pages are well organized, their structure should be preserved in the output format.
- Each page should return a single document section with all the page's content as subsections inside it.
- Use consistent section keys for all pages
- Pages can contain one or more titles with nested subtitles, their relationship should be well respected.
- Pages can contain single column or multicolumn text
- Pages can contain lists in a bullet point, numeric, or any format. Try to use a unified format for them. 
- Pages can contain one or more tables, with or without additional text that doesn’t belong to the table. 
- For each table, identify its content and caption. 
- If the page contains tables and paragraphs, return both. 
"""

COMMON_ISSUES = """
- You mistake tables for sections and subsections. Make sure to identify tables and sections separately.
- Some two-column texts have line-wide tables, and vice versa. Do not be confused by it. 
- Avoid removing an entire column and pretend that is doesn't exist
- Avoid forgetting   begin documt and end document latex tags 
"""

PROMPT = """
{role_msg}

The following are prior information about the structure of the input documents. You should pay attention to them and use them to better convert the input file to the target formats:
{input_structure_notes}

The following are common mistakes that you used to do. Avoid them as much as you can:
{common_pitfalls}

Return only the {tgt_format} with no explanation text.
""".format(role_msg=SYSTEM_ROLE, input_structure_notes=INPUT_STRUCTURE, common_pitfalls=COMMON_ISSUES, tgt_format = TARGET_FORMAT)
