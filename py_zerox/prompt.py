PROMPT  = r"""
You are a system that converts PDF files to Latex.
Follow these guidelines for an effective conversion:

General guidelines:
- The PDF is given a a sequence of images; Convert them together and respect their sequence.
- Keep the original pages structure in the output.
- Use consistent section headings for all pages.
- For each page, check if it is a continuance of the hierarchy from the previous page.
- Respect the hierarchy of titles and subtitles using the following order: [ "section", "subsection", "subsubsection", "paragraph" ]
- A section, subsection, subsubsection, or a paragraph can start at a page and end in a following page.
- Standardize lists (bullet points, numbers, etc.) into a unified format.
- If a page has both tables and text, include both.
- Correctly escape special latex characters such as: & | % in order not to disrupt the latex parsing and rendering.
- Ignore special formatting latex such as \quad, \bigskip, \href, \underline etc
- Do not output sections, subsections or header that do not exist in the document.
- Do not output any latex comments

Tables guidelines:
- Plan tables ahead: output metadata for tables (number of columns and rows, what are the column headers, etc). Output the metadata in a separate section denoted by \tablemeta{...} where the elipses are placeholders for the metadata
- Use the table meta data to identify and format all tables including their content.
- Output the table latex.
- Output the column headers as a row.
- Be aware of column spans and row spans in tables.

Avoid these mistakes:
- Don NOT output tables as sections or subsections.
- Tables should have consistent unmber of columns. 
- Be careful with two-column texts that have line-wide tables and vice versa. 
- Do not remove spaces from section headers (e.g. \section{ThisIsHeader} is NOT correct, it should be \section{This is Header} )

Return only the Latex with no explanation.
"""


POST_PROCESSING_PROMP = """
-Identify any table-like structures in the LaTeX code that lack a \begin{tabular} tag. Convert these structures to tables and with the tag \begin{tabular}{(and inside is only the charceters r, l, c, |)}, ensuring there’s only an only set of curly braces after \begin{tabular}, and that the braces contain only the alignment options l, r, or c. Exclude any other tabular attributes.

-Remove all LaTeX comments entirely.

-Restore escaped characters: Ensure special characters like %, $, &, #, _, {, }, ~, and ^ are properly escaped (e.g., \%, \$, \&), but avoid escaping symbols that are part of LaTeX syntax, such as & within tables.

-Remove all HTML tags: Strip out any HTML tags present in the LaTeX code to prevent conflicts or unintended formatting.

-Identify and remove all optional tags within square brackets [...] from LaTeX commands, so that each tag contains only its essential structure.

-For tabular structures:
    1. Analyze the Table Structure:
    - Examine the table, including the tabular environment, column definitions, row entries, and any \\multicolumn commands.
    - Count the columns defined in the tabular environment and verify that each row contains the same number of columns.

    2. Correct the Column Specification:
    - Adjust the column structure in the tabular environment (|l|r|r|...) to match the number of columns in the rows. Count each row’s columns by counting & symbols plus \\multicolumn spans.
    - Ensure that each row has the correct number of columns, as specified in the tabular environment.

    3. Fix \\multicolumn Span Issues:
    - Check each row to ensure the total number of columns remains consistent, even when \\multicolumn commands are used. The combined \\multicolumn spans and individual columns should match the column count in the tabular environment.
    - If a row has fewer columns than specified, either:
        - Increase the \\multicolumn spans to cover more columns, or
        - Add empty columns (&) at the end of the row to reach the required column count.

        Example Fix for \\multicolumn Mismatch:
            Consider this row:
            & \multicolumn{2}{|c|}{Text} & \multicolumn{2}{|c|}{text} \\
            ### Issue

            If the table has **seven columns** defined in the `tabular` environment, this row does not meet that requirement. The `\multicolumn{2}{|c|}{...}` commands each cover **two columns**, totaling **four columns**. Combined with the single column represented by the initial `&`, this row only covers **five columns** instead of the required seven.

            ### Solution options:
            Here are two ways to fix this you must chose one of them:

            1. **Increase the `\multicolumn` spans**: 

                If we want the grouped headers to span more columns, adjust each `\multicolumn` to cover three columns instead of two:

                & \multicolumn{3}{|c|}{Text} & \multicolumn{3}{|c|}{text} \\

                Now, the initial `&` (1 column) plus two `\multicolumn{3}{|c|}{...}` spans (3 columns each) total **seven columns**, matching the column count.

            2. **Add empty columns**:

                If the spans should stay as two columns each, add two empty columns (e.g., `&`) to complete the row count:

                & \multicolumn{2}{|c|}{Text} & \multicolumn{2}{|c|}{Text} & & \\

                Now, the row has **seven columns**: 1 column for the initial `&`, two `\multicolumn{2}{|c|}{...}` spans, plus two empty columns (`& &`). This ensures a consistent column count across all rows.

    4. Verify the Table Structure again by counting the columns in each row and comparing them to the tabular environment’s column definition after the fixes.
        Ensure that the table structure is consistent and that all rows have the correct number of columns and if not repeat the process.:
"""

