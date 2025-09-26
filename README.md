# Notion Export to PDF Conversion Guide

This document provides instructions on how to use the `process_notion_export.py` script to convert a Notion export into a single, self-contained PDF file.

The script performs several key actions:
1.  Finds all images within the Notion export folder.
2.  Converts, resizes (to 720p), and compresses them into a `processed_images` directory to reduce file size.
3.  Creates a new HTML file (`converted.html`) with updated image links.
4.  Adds a linked image gallery at the end of the document for easy reference.
5.  Converts the newly generated HTML file into a final PDF (`converted.pdf`).

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1.  **Python 3:** If you don't have it, download it from [python.org](https://www.python.org/).
2.  **wkhtmltopdf:** This is a command-line tool required by the script to generate PDFs from HTML. **This is a critical dependency.**

    *   **macOS (using Homebrew):**
        ```bash
        brew install wkhtmltopdf
        ```
    *   **Windows/Linux:**
        Download the appropriate installer from the [official wkhtmltopdf website](https://wkhtmltopdf.org/downloads.html). During installation, ensure you add the tool to your system's PATH.

## Setup

1.  **Create a Virtual Environment:**
    Open your terminal in the project directory (`notion-pdf`) and run the following command to create a virtual environment. This isolates the project's dependencies.
    ```bash
    python3 -m venv venv
    ```

2.  **Activate the Virtual Environment:**
    *   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    *   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    Your terminal prompt should now be prefixed with `(venv)`.

3.  **Install Dependencies:**
    Install the necessary Python libraries using this command:
    ```bash
    pip install beautifulsoup4 Pillow pillow-heif pdfkit
    ```

## Usage

1.  **Locate Your Notion HTML File:**
    Inside your unzipped Notion export (e.g., the `Private & Shared-1` folder), find the main `.html` file.

2.  **Run the Script:**
    Execute the script from your terminal, providing the relative path to the main Notion export HTML file.

    **Example based on your folder structure:**
    ```bash
    python process_notion_export.py "Private & Shared-1/250728 SVM ORB Comprehensive Maintenance 2 23e331501d3b80f286b8efaa1e9ed1dc.html"
    ```

## Output

After the script finishes, you will find the following new items in your project's root directory:

*   `processed_images/`: A folder containing all the optimized images from your export.
*   `converted.html`: An intermediate HTML file with updated image paths and the new gallery.
*   `converted.pdf`: The final, processed PDF document.

## Troubleshooting

*   **`FileNotFoundError` for `wkhtmltopdf`:** If you see an error message stating `wkhtmltopdf` is not found, it means the tool is either not installed or not accessible from your system's PATH. Please reinstall it following the instructions in the "Prerequisites" section. You can usually ignore this error.
