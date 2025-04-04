from flask import Flask, jsonify, render_template, request, send_file, Response
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import io
import re
from presidio_anonymizer.operators import Decrypt

app = Flask(__name__)

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()


def decrypt_content(text: str, key: str) -> str:
    def find_base64_strings(text):
        base64_pattern = r'(?:[A-Za-z0-9+/]{4}){10,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?'
        matches = re.findall(base64_pattern, text)
        matches = [m for m in matches if len(m) >= 44]
        return matches

    base64_strings = find_base64_strings(text)
    for base64_string in base64_strings:
        try:
            decrypted_result = Decrypt().operate(text=base64_string, params={"key": key})
            text = text.replace(base64_string, decrypted_result)
        except Exception as e:
            print(f"Error decrypting: {base64_string} - {e}")
    return text


def anonymize_content(text: str, mode: str = 'default', key: str = None):
    if mode == 'decrypt':
        if not key:
            raise ValueError("Decryption key is required for decrypt mode.")
        decrypted_text = decrypt_content(text, key)
        return decrypted_text
    else:
        results = analyzer.analyze(text=text, language='en')

        if mode == 'mask':
            operator_config = {"DEFAULT": OperatorConfig("replace", {"new_value": "***"})}
        elif mode == 'encrypt':
            if not key:
                raise ValueError("Encryption key is required for encrypt mode.")
            operator_config = {"DEFAULT": OperatorConfig("encrypt", {"key": key})}
        else:
            operator_config = None

        if operator_config:
            anonymized_result = anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators=operator_config
            )
        else:
            anonymized_result = anonymizer.anonymize(
                text=text,
                analyzer_results=results
            )

        return anonymized_result.text


@app.route('/')
def index():
    return render_template('index.html', active_tab='text')


@app.route('/anonymize_text', methods=['POST'])
def anonymize_text():
    text = request.form['text']
    mode = request.form.get('mode', 'default')
    key = request.form.get('key')

    try:
        anonymized_text = anonymize_content(text, mode, key)
        return render_template('index.html', 
                               anonymized_text=anonymized_text, 
                               input_text=text, 
                               mode=mode, 
                               key=key, 
                               active_tab='text')
    except Exception as e:
        error_message = str(e)
        if error_message == "Invalid input, key must be of length 128, 192 or 256 bits":
            error_message = "Invalid input, key must be of length 16, 24 or 32 characters"
        return render_template('index.html', 
                               input_text=text, 
                               mode=mode, 
                               key=key, 
                               error_message=error_message, 
                               active_tab='text')


@app.route('/anonymize_csv', methods=['POST'])
def anonymize_csv():
    file = request.files['file']
    mode = request.form.get('mode', 'default')
    key = request.form.get('key')

    try:
        contents = file.read().decode('utf-8')

        anonymized_text = anonymize_content(contents, mode, key)

        output_io = io.StringIO(anonymized_text)
        return Response(output_io.getvalue(), mimetype='text/csv', headers={
            "Content-Disposition": f"attachment;filename=processed_{file.filename}"
        })
    except Exception as e:
        error_message = str(e)
        return render_template('index.html', 
                               error_message=error_message, 
                               mode=mode, 
                               key=key, 
                               active_tab='csv')


@app.route('/api/anonymize_text', methods=['POST'])
def api_anonymize_text():
    # Support for JSON
    if request.is_json:
        data = request.get_json()
        text = data.get('text', '')
        mode = data.get('mode', 'default')
        key = data.get('key')
    else:
        # Support for form data 
        text = request.form.get('text', '')
        mode = request.form.get('mode', 'default')
        key = request.form.get('key')
    
    try:
        anonymized_text = anonymize_content(text, mode, key)
        return jsonify({
            'status': 'success',
            'anonymized_text': anonymized_text
        })
    except Exception as e:
        error_message = str(e)
        if error_message == "Invalid input, key must be of length 128, 192 or 256 bits":
            error_message = "Invalid input, key must be of length 16, 24 or 32 characters"
        return jsonify({
            'status': 'error',
            'error': error_message
        }), 400

@app.route('/api/anonymize_csv', methods=['POST'])
def api_anonymize_csv():
    file = request.files['file']
    mode = request.form.get('mode', 'default')
    key = request.form.get('key')

    try:
        contents = file.read().decode('utf-8')

        anonymized_text = anonymize_content(contents, mode, key)

        output_io = io.StringIO(anonymized_text)
        return Response(output_io.getvalue(), mimetype='text/csv', headers={
            "Content-Disposition": f"attachment;filename=processed_{file.filename}"
        })
    except Exception as e:
        error_message = str(e)
        return jsonify({
            'status': 'error',
            'error': error_message
        }), 400

@app.route('/api/docs')
def api_docs():
    return render_template('api_docs.html')

if __name__ == '__main__':
    app.run(port=8082, host='0.0.0.0')
