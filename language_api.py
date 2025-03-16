from flask import Blueprint, request, jsonify
from google.cloud import translate_v2 as translate
import os

language_bp = Blueprint('language_bp', __name__)

app_translate_client = None

@language_bp.before_app_first_request
def initialize_translate_client():
    global app_translate_client
    app_translate_client = translate.Client()

@language_bp.route('/translate', methods=['POST'])
def translate_text_route():
    data = request.get_json()
    text = data.get('text')
    target_language = data.get('target_language', 'en')

    if not text:
        return jsonify({"translated_text": ""})

    try:
        result = app_translate_client.translate(text, target_language=target_language)
        return jsonify({"translated_text": result["translatedText"]})
    except Exception as e:
        print(f"Translation error: {e}")
        return jsonify({"translated_text": None, "error": str(e)}), 500