from flask import Flask, request, send_from_directory, jsonify
import os
import testkgp as pdf_processor

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400

    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded.pdf'))
    return 'File uploaded successfully', 200

@app.route('/uploads/<path:filename>')
def serve_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return 'No file part', 400

    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    file_content = file.read().decode('utf-8')
    answers = pdf_processor.process_pdf(file_content)
    return jsonify(answers)

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True)
