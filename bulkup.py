from flask import Flask, request, send_file, render_template, redirect, url_for
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import markdown
from io import BytesIO
import os

def clean_string(s):
    """Utility function to clean and strip strings"""
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

    for i, row in csv_data.iterrows():
        post_id = i + 1
        slug = row['Slug']
        title = row['Title']
        content = row['Content']
        date = pd.to_datetime(row['Date'], errors='coerce')

        if pd.isna(date):
            date = datetime.now()

        author = row['Author']
        categories = row['Categories']
        tags = row['Tags']
        image_url = row['Image_url']
        attachments = row['Attachments']

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

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download-template')
def download_template():
    df_template = pd.DataFrame({
        'Title': [],
        'Slug': [],
        'Content': [],
        'Date': [],
        'Author': [],
        'Categories': [],
        'Tags': [],
        'Image_url': [],
        'Attachments': []
    })
    csv_path = 'template.csv'
    df_template.to_csv(csv_path, index=False)
    return send_file(csv_path, as_attachment=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        csv_data = pd.read_csv(file)
        csv_data['Title'] = csv_data['Title'].apply(clean_string)
        csv_data['Slug'] = csv_data['Slug'].apply(clean_string)
        csv_data['Content'] = csv_data['Content'].apply(clean_string)
        csv_data['Date'] = pd.to_datetime(csv_data['Date'], errors='coerce')
        csv_data['Author'] = csv_data['Author'].apply(clean_string)
        csv_data['Categories'] = csv_data['Categories'].apply(clean_string)
        csv_data['Tags'] = csv_data['Tags'].apply(clean_string)
        csv_data['Image_url'] = csv_data['Image_url'].apply(clean_string)
        csv_data['Attachments'] = csv_data['Attachments'].apply(clean_string)
        
        xml_str = generate_xml(csv_data)
        xml_bytes = BytesIO(xml_str.encode('utf-8'))
        xml_bytes.seek(0)

        return send_file(
            xml_bytes,
            mimetype='application/octet-stream',
            as_attachment=True,
            attachment_filename='blog_posts.xml'
        )

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
