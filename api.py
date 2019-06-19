from flask import Flask, jsonify, request,render_template,json
from bs4 import BeautifulSoup
import requests
import os
from dotenv import load_dotenv
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
TEXTRAZOR_API_KEY = os.getenv('TEXTRAZOR_API_KEY')

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Google Natural Language API Test</h1>'
@app.route("/api/nl-process", methods=['GET', 'POST'])
def sendGoogle():
    if request.method == 'POST':
        ret = request.get_json()
        soup = BeautifulSoup(ret['code'], 'html.parser')
        [s.extract() for s in soup('script')]
        [s.extract() for s in soup('style')]
        print(soup.get_text())
        wordlength = len(soup.get_text())
   
        GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        # google natural language api

        headers_gnl = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        data_gnl = "{  \"document\":{ \"type\": \"PLAIN_TEXT\", \"content\":\""+soup.get_text()+"\"  }"+"}"

        
        response_entities = requests.post('https://language.googleapis.com/v1/documents:analyzeEntities?fields=entities%2Clanguage&key='+GOOGLE_API_KEY, headers=headers_gnl, data=data_gnl.encode('utf-8'))
        response_categories= requests.post('https://language.googleapis.com/v1/documents:classifyText?key='+GOOGLE_API_KEY, headers=headers_gnl, data=data_gnl.encode('utf-8'))
        ret_response_entities = json.loads(response_entities.text)
        ret_response_categories = json.loads(response_categories.text)
        print('ret_response_categories',ret_response_categories)
        return jsonify({
            'numbers' : wordlength,
            'words' : soup.get_text(),
            'json' : {
                'entities' : ret_response_entities,
                'categories' : ret_response_categories
             }
        })
    return render_template('index.html')

@app.route("/api/textrazor-process", methods=['GET', 'POST'])
def sendTextrazor():
    print('sendTextrazor')
    if request.method == 'POST':
        ret = request.get_json()
        soup = BeautifulSoup(ret['code'], 'html.parser')
        [s.extract() for s in soup('script')]
        [s.extract() for s in soup('style')]
        print(soup.get_text())
        wordlength = len(soup.get_text())
        # textrazor part
        TEXTRAZOR_API_KEY = os.getenv('TEXTRAZOR_API_KEY')
        headers_textrazor = {
            'x-textrazor-key': TEXTRAZOR_API_KEY,
        }
        data_textrazor = {
            'extractors':'entities,categories',
            'classifiers':'textrazor_newscodes',
            'text': soup.get_text()
        }
        response_textrazor = requests.post('https://api.textrazor.com/', headers=headers_textrazor, data=data_textrazor)
        ret_response_textrazor = json.loads(response_textrazor.text)
        print('ret_response_textrazor',ret_response_textrazor['response'])
        return jsonify({
            'numbers' : wordlength,
            'words' : soup.get_text(),
            'json' : ret_response_textrazor['response'],
        })

    return render_template('index.html')
    
if __name__ == '__main__':
    app.run(debug=True)


