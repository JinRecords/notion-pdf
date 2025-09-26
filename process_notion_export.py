import os
import shutil
import re
from PIL import Image
from bs4 import BeautifulSoup
import uuid
import pillow_heif
from urllib.parse import unquote
import io
import pdfkit

def process_notion_export(html_file_path, output_html_name="converted.html"):
    """
    Processes a Notion export to rename, compress, and move images,
    and then updates an HTML file to reflect these changes and adds an image gallery.
    """
    html_file_path = os.path.abspath(html_file_path)
    project_root = os.path.dirname(os.path.dirname(html_file_path))
    base_dir = os.path.dirname(html_file_path)
    processed_images_dir = os.path.join(project_root, "processed_images")
    shutil.rmtree(processed_images_dir, ignore_errors=True)
    os.makedirs(processed_images_dir, exist_ok=True)

    image_map = {}
    image_counter = 1
    gallery_images = []

    # Find all images and process them
    for root, _, files in os.walk(base_dir):
        for file in files:
            original_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()

            if file_ext in ['.jpg', '.jpeg', '.png', '.heic', '.gif', '.bmp']:
                try:
                    new_name = f"image_{image_counter}.jpeg"
                    new_path = os.path.join(processed_images_dir, new_name)
                    
                    while os.path.exists(new_path):
                        new_name = f"image_{image_counter}_{uuid.uuid4().hex[:4]}.jpeg"
                        new_path = os.path.join(processed_images_dir, new_name)

                    if file_ext == '.heic':
                        heif_file = pillow_heif.read_heif(original_path)
                        img = Image.frombytes(
                            heif_file.mode, heif_file.size, heif_file.data, "raw")
                    else:
                        img = Image.open(original_path)

                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # Resize to 720p while maintaining aspect ratio
                    target_width, target_height = 1280, 720
                    ratio = min(target_width / img.width, target_height / img.height)
                    if ratio < 1:
                        new_size = (int(img.width * ratio), int(img.height * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)

                    # Compress to under 300KB
                    buffer = io.BytesIO()
                    quality = 85
                    img.save(buffer, format="JPEG", quality=quality, optimize=True)
                    while buffer.getbuffer().nbytes > 300000 and quality > 20:
                        quality -= 5
                        buffer = io.BytesIO()
                        img.save(buffer, format="JPEG", quality=quality, optimize=True)
                    
                    with open(new_path, 'wb') as f:
                        f.write(buffer.getvalue())

                    relative_original_path = os.path.relpath(original_path, base_dir)
                    relative_new_path = os.path.relpath(new_path, project_root)
                    
                    image_map[relative_original_path] = relative_new_path
                    
                    if not file.startswith("my-notion-face"):
                        gallery_images.append(relative_new_path)

                    image_counter += 1
                except Exception as e:
                    print(f"Could not process image {original_path}: {e}")

    # Process the HTML file
    with open(html_file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Update image references in the main content
    for img_tag in soup.find_all('img'):
        original_src = img_tag.get('src')
        if original_src:
            unquoted_src = unquote(original_src)
            if unquoted_src in image_map:
                new_src = image_map[unquoted_src]
                img_tag['src'] = new_src

                if not unquoted_src.startswith("my-notion-face"):
                    gallery_anchor = f"#{os.path.splitext(os.path.basename(new_src))[0]}"
                    parent_a = img_tag.find_parent('a')
                    if parent_a:
                        parent_a['href'] = gallery_anchor
                    else:
                        a_tag = soup.new_tag('a', href=gallery_anchor)
                        img_tag.wrap(a_tag)

    # Create the image gallery
    gallery_section = soup.new_tag('div', **{'class': 'image-gallery'})
    gallery_header = soup.new_tag('h2')
    gallery_header.string = "Image gallery"
    gallery_section.append(gallery_header)

    for i, img_path in enumerate(gallery_images):
        if i % 9 == 0:
            table = soup.new_tag('table', **{'class': 'image-table'})
            gallery_section.append(table)
            if i > 0:
                table['style'] = 'page-break-before: always;'

        if i % 3 == 0:
            tr = soup.new_tag('tr')
            table.append(tr)

        td = soup.new_tag('td')
        figure = soup.new_tag('figure', id=os.path.splitext(os.path.basename(img_path))[0])
        img_tag = soup.new_tag('img', src=img_path, alt=f"Figure {i+1}", style="width: 100%;")
        figcaption = soup.new_tag('figcaption')
        figcaption.string = f"Figure {i+1}"
        
        figure.append(img_tag)
        figure.append(figcaption)
        td.append(figure)
        tr.append(td)

    soup.body.append(gallery_section)
    
    # Add some basic styling for the gallery
    style_tag = soup.new_tag('style')
    style_tag.string = """
        .image-gallery table {
            width: 100%;
            border-collapse: collapse;
        }
        .image-gallery td {
            border: 1px solid white;
            padding: 5px;
            text-align: center;
            width: 33.33%;
        }
        .image-gallery figure {
            margin: 0;
        }
        @media print {
            .image-table {
                page-break-inside: avoid;
            }
        }
    """
    soup.head.append(style_tag)


    # Write the new HTML file
    output_html_path = os.path.join(project_root, output_html_name)
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f"Processing complete. New HTML file created at: {output_html_path}")

    # For PDF conversion, make image paths absolute
    pdf_soup = BeautifulSoup(str(soup), 'html.parser')
    for img_tag in pdf_soup.find_all('img'):
        img_src = img_tag.get('src')
        if img_src and not img_src.startswith(('http://', 'https://', 'file://')):
            absolute_img_path = os.path.join(project_root, img_src)
            img_tag['src'] = f'file://{absolute_img_path}'

    # Convert HTML to PDF
    try:
        pdf_options = {
            'enable-local-file-access': None,
            'enable-internal-links': True,
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
        }
        output_pdf_path = os.path.join(project_root, 'converted.pdf')
        pdfkit.from_string(str(pdf_soup), output_pdf_path, options=pdf_options)
        print(f"Successfully created PDF: {output_pdf_path}")
    except FileNotFoundError:
        print("PDF conversion failed. Please ensure wkhtmltopdf is installed and in your system's PATH.")
    except Exception as e:
        if "ContentNotFoundError" in str(e):
            print("Ignoring ContentNotFoundError during PDF conversion.")
        else:
            print(f"An error occurred during PDF conversion: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python process_notion_export.py <path_to_html_file>")
        sys.exit(1)
    html_file_path = sys.argv[1]
    process_notion_export(html_file_path)
