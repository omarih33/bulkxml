from flask import Flask, request, send_file, render_template, redirect, flash, url_for
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import markdown
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

def clean_string(s):
    if pd.isna(s):
        return ''
    return str(s).strip()

def generate_xml(csv_data):
    rss = ET.Element('rss', attrib={
        "xmlns:excerpt": "http://wordpress.org/export/1.2/excerpt/",
        "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
        "xmlns:wfw": "http://wellformedweb.org/CommentAPI/",
        "xmlns:dc": "http://purl.org/dc/elements/1.1/",
        "xmlns:wp": "http://wordpress.org/export/1.2/"
    })

    channel = ET.SubElement(rss, 'channel')

    title = ET.SubElement(channel, 'title')
    title.text = "Blog Posts"

    link = ET.SubElement(channel, 'link')
    link.text = "https://yourblog.com"

    pubDate = ET.SubElement(channel, 'pubDate')
    pubDate.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

    description = ET.SubElement(channel, 'description')
    description.text = ""

    language = ET.SubElement(channel, 'language')
    language.text = "en-US"

    wxr_version = ET.SubElement(channel, 'wp:wxr_version')
    wxr_version.text = "1.2"

    author_elem = ET.SubElement(channel, 'wp:author')

    author_id = ET.SubElement(author_elem, 'wp:author_id')
    author_id.text = "1"

    author_login = ET.SubElement(author_elem, 'wp:author_login')
    author_login.text = "admin"

    author_email = ET.SubElement(author_elem, 'wp:author_email')
    author_email.text = "admin@yourblog.com"

    author_display_name = ET.SubElement(author_elem, 'wp:author_display_name')
    author_display_name.text = "Admin"

    author_first_name = ET.SubElement(author_elem, 'wp:author_first_name')
    author_first_name.text = "Admin"

    author_last_name = ET.SubElement(author_elem, 'wp:author_last_name')
    author_last_name.text = ""

    for post_id, (_, row) in enumerate(csv_data.iterrows(), start=1):
        slug = clean_string(row.get('Slug', ''))
        title = clean_string(row.get('Title', ''))
        content = clean_string(row.get('Content', ''))
        date = pd.to_datetime(row.get('Date', datetime.now()), errors='coerce')

        if pd.isna(date):
            date = datetime.now()

        author = clean_string(row.get('Author', ''))
        categories = clean_string(row.get('Categories', ''))
        tags = clean_string(row.get('Tags', ''))
        image_url = clean_string(row.get('Image_url', '')) 
        attachments = clean_string(row.get('Attachments', ''))

        item = ET.Element('item')

        guid = ET.SubElement(item, 'guid', attrib={"isPermaLink": "false"})
        guid.text = f"/{slug}"

        title_elem = ET.SubElement(item, 'title')
        title_elem.text = title

        link_elem = ET.SubElement(item, 'link')
        link_elem.text = f"/{slug}"

        post_name = ET.SubElement(item, 'wp:post_name')
        post_name.text = slug

        post_type = ET.SubElement(item, 'wp:post_type')
        post_type.text = "post"

        post_id_elem = ET.SubElement(item, 'wp:post_id')
        post_id_elem.text = str(post_id)

        status = ET.SubElement(item, 'wp:status')
        status.text = "publish"

        pubDate = ET.SubElement(item, 'pubDate')
        pubDate.text = date.strftime("%a, %d %b %Y %H:%M:%S +0000")

        post_date = ET.SubElement(item, 'wp:post_date')
        post_date.text = date.strftime("%Y-%m-%d %H:%M:%S")

        post_date_gmt = ET.SubElement(item, 'wp:post_date_gmt')
        post_date_gmt.text = post_date.text

        dc_creator = ET.SubElement(item, 'dc:creator')
        dc_creator.text = author

        comment_status = ET.SubElement(item, 'wp:comment_status')
        comment_status.text = "open"

        ping_status = ET.SubElement(item, 'wp:ping_status')
        ping_status.text = "open"

        for category in categories.split(','):
            category = clean_string(category)
            if category:
                cat_elem = ET.SubElement(item, 'category', domain="category", nicename=category.lower().replace(' ', '-'))
                cat_elem.text = category

        for tag in tags.split(','):
            tag = clean_string(tag)
            if tag:
                tag_elem = ET.SubElement(item, 'category', domain="post_tag", nicename=tag.lower().replace(' ', '-'))
                tag_elem.text = tag

        html_content = markdown.markdown(content)

        content_encoded = ET.SubElement(item, 'content:encoded')
        content_encoded.text = html_content

        postmeta_thumbnail = ET.SubElement(item, 'wp:postmeta')
        meta_key_thumbnail = ET.SubElement(postmeta_thumbnail, 'wp:meta_key')
        meta_key_thumbnail.text = "_thumbnail_id"
        meta_value_thumbnail = ET.SubElement(postmeta_thumbnail, 'wp:meta_value')
        meta_value_thumbnail.text = str(post_id + 1000)

        channel.append(item)

        item = ET.Element('item')

        title_elem = ET.SubElement(item, 'title')
        title_elem.text = f"Attachment for post {post_id}"

        link_elem = ET.SubElement(item, 'link')
        link_elem.text = image_url

        attachment_url = ET.SubElement(item, 'wp:attachment_url')
        attachment_url.text = image_url

        post_id_elem = ET.SubElement(item, 'wp:post_id')
        post_id_elem.text = str(post_id + 1000)

        post_date = ET.SubElement(item, 'wp:post_date')
        post_date.text = date.strftime("%Y-%m-%d %H:%M:%S")

        post_date_gmt = ET.SubElement(item, 'wp:post_date_gmt')
        post_date_gmt.text = post_date.text

        post_type = ET.SubElement(item, 'wp:post_type')
        post_type.text = "attachment"

        post_mime_type = ET.SubElement(item, 'wp:post_mime_type')
        post_mime_type.text = "image/jpeg"

        status = ET.SubElement(item, 'wp:status')
        status.text = "inherit"

        channel.append(item)

    tree = ET.ElementTree(rss)
    output = BytesIO()
    tree.write(output, encoding="utf-8", xml_declaration=True)
    xml_str = output.getvalue()
    return xml_str

@app.route('/')
def home():
    return render_template('tool.html')  # Ensure this matches your template file's name

@app.route('/converter')
def converter():
    return render_template('tool.html')  # Ensure this matches your template file's name

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        flash('This URL is for file uploads only. Please upload a CSV file.', 'error')
        return redirect(url_for('converter'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part. Please upload a valid CSV file.', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file. Please select a CSV file.', 'error')
            return redirect(request.url)

        try:
            csv_data = pd.read_csv(file)
        except Exception as e:
            flash('There was an error reading the file. Please check the format and try again.', 'error')
            return redirect(request.url)

        required_columns = ['Title', 'Slug', 'Content', 'Date', 'Author', 'Categories', 'Tags', 'Image_url', 'Attachments']
        if not all(column in csv_data.columns for column in required_columns):
            flash('The uploaded CSV file is missing columns. Please ensure it contains the required columns: ' + ', '.join(required_columns), 'error')
            return redirect(request.url)

        # Cleaning the data
        csv_data['Title'] = csv_data['Title'].apply(clean_string)
        csv_data['Slug'] = csv_data['Slug'].apply(clean_string)
        csv_data['Content'] = csv_data['Content'].apply(clean_string)
        csv_data['Date'] = pd.to_datetime(csv_data['Date'], errors='coerce')
        csv_data['Author'] = csv_data['Author'].apply(clean_string)
        csv_data['Categories'] = csv_data['Categories'].apply(clean_string)
        csv_data['Tags'] = csv_data['Tags'].apply(clean_string)
        csv_data['Image_url'] = csv_data['Image_url'].apply(clean_string)
        csv_data['Attachments'] = csv_data['Attachments'].apply(clean_string)

        try:
            xml_str = generate_xml(csv_data)
            xml_filename = 'blog_posts.xml'
            
            with open(xml_filename, 'wb') as f:
                f.write(xml_str)
            
            return send_file(xml_filename, as_attachment=True)
        except Exception as e:
            flash('There was an error generating the XML file. Please try again or contact support@sqspthemes.com for assistance.', 'error')
            return redirect(request.url)

@app.after_request
def remove_file(response):
    try:
        if os.path.exists('template.csv'):
            os.remove('template.csv')
        if os.path.exists('blog_posts.xml'):
            os.remove('blog_posts.xml')
    except Exception as e:
        app.logger.error(f"Error removing or closing downloaded file handle: {e}")
    return response

if __name__ == '__main__':
    app.run(debug=True)
