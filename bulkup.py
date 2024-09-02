from flask import Flask, request, send_file, render_template, redirect, url_for, send_from_directory, flash
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import markdown
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

def clean_string(s):
    """Utility function to clean and strip strings"""
    if pd.isna(s):
        return ''
    return str(s).strip()

def validate_csv_headers(csv_data, required_headers):
    """Validate that the CSV file has the required headers"""
    missing_headers = [header for header in required_headers if header not in csv_data.columns]
    return missing_headers

def validate_data(csv_data):
    """Validate the data types and required fields"""
    errors = []

    # Check for required fields
    for index, row in csv_data.iterrows():
        if not row['Title'] or not row['Slug'] or not row['Content']:
            errors.append(f"Row {index + 1} is missing required fields.")

    # Check for valid dates
    for index, date in csv_data['Date'].iteritems():
        if pd.isna(date):
            errors.append(f"Row {index + 1} has an invalid date.")

    # Check for duplicate slugs
    if csv_data['Slug'].duplicated().any():
        errors.append("Duplicate slugs found in the CSV file.")

    return errors

def generate_xml(csv_data):
    # (Existing XML generation code here)
    pass

@app.route('/')
def home():
    return send_from_directory('static', 'home.html')

@app.route('/converter')
def converter():
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
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if not file.filename.endswith('.csv'):
        flash('Invalid file type. Please upload a CSV file.')
        return redirect(request.url)

    if file:
        try:
            csv_data = pd.read_csv(file)
        except Exception as e:
            flash(f"Error reading CSV file: {e}")
            return redirect(request.url)

        # Validate CSV headers
        required_headers = ['Title', 'Slug', 'Content', 'Date', 'Author', 'Categories', 'Tags', 'Image_url', 'Attachments']
        missing_headers = validate_csv_headers(csv_data, required_headers)
        if missing_headers:
            flash(f"Missing required headers: {', '.join(missing_headers)}")
            return redirect(request.url)

        # Validate CSV data
        data_errors = validate_data(csv_data)
        if data_errors:
            for error in data_errors:
                flash(error)
            return redirect(request.url)

        # Clean and process the data
        csv_data['Title'] = csv_data['Title'].apply(clean_string)
        csv_data['Slug'] = csv_data['Slug'].apply(clean_string)
        csv_data['Content'] = csv_data['Content'].apply(clean_string)
        csv_data['Date'] = pd.to_datetime(csv_data['Date'], errors='coerce')
        csv_data['Author'] = csv_data['Author'].apply(clean_string)
        csv_data['Categories'] = csv_data['Categories'].apply(clean_string)
        csv_data['Tags'] = csv_data['Tags'].apply(clean_string)
        csv_data['Image_url'] = csv_data['Image_url'].apply(clean_string)
        csv_data['Attachments'] = csv_data['Attachments'].apply(clean_string)

        # Generate the XML
        xml_str = generate_xml(csv_data)
        xml_filename = 'blog_posts.xml'

        with open(xml_filename, 'wb') as f:
            f.write(xml_str)

        return send_file(xml_filename, as_attachment=True)

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

# Error handling
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
