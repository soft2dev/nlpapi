from flask import Flask, jsonify, request,render_template,json
from bs4 import BeautifulSoup
from jinja2 import Template
from dotenv import load_dotenv

import requests
import os
from urllib.request import urlopen
import re

APP_ROOT = os.path.join(os.path.dirname(__file__), '..')   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
TEXTRAZOR_API_KEY = os.getenv('TEXTRAZOR_API_KEY')

app = Flask(__name__) 

def strRange(input_text):
    seperator = ' '
    input_text = seperator.join(input_text.split())
    return input_text
def dictEntityRange(dictEntity):
    return sorted(dictEntity, key = lambda entity: entity['name'],reverse=True)

def convertTag(entity):
  return {
    "isReplace": 0,
    "text": entity['name'],
    "tag": 'span',
    "class": 'FONT_'+entity['type']+'_COLOR'
  }

def createDomEntity(input_text,common_entities):
    output_text = ''
    for index, obj in enumerate(common_entities):
        key = obj['text']
        if  obj['isReplace'] == 0:
            if  wordInString(key, input_text):
                index_num = input_text.find(key)
                new_text = '<span class="entity"><span class="entity-annotation">⟨</span><span class="{}">{}</span><span class="entity-annotation">⟩<sub class="sub-color">{}</sub></span></span>'.format(obj['class'], key,index+1)
                new_text_length = len(new_text)
                input_text = input_text[:index_num] + new_text + input_text[index_num + len(key):]
                if len(output_text) == 0:
                    output_text = input_text
                else:
                    output_text = output_text[:index_num] + new_text + output_text[index_num + len(key):]
                
                input_text = input_text.replace(new_text, ' ' * new_text_length)
                obj['isReplace'] = 1
    return output_text  

def wordInString(word, string_value):
    return True if re.search(r'\b' + word + r'\b', string_value) else False

@app.route('/')
def sendGoogle():
    target_link = 'https://www.momsstrollerreviews.com/moms-picks-top-20-best-strollers-for-2018'
    competitor_links = [
        'https://www.walmart.com/cp/strollers/118134',
        'https://www.target.com/c/strollers-baby/-/n-5xtk7',
        'https://www.buybuybaby.com/store/category/strollers/strollers/32572/',
        'https://www.amazon.com/baby-strollers-tandem-jogger-double-triple/b?ie=utf8&node=166842011',
        'https://www.amazon.com/best-sellers-baby-strollers/zgbs/baby-products/166842011',
        'http://www.gracobaby.com/en-US',
    ]

    # html parse
    target_html = requests.get(target_link)
    target_soup = BeautifulSoup(target_html.text, 'html.parser')
    [s.extract() for s in target_soup('img')]
    [s.extract() for s in target_soup('script')]
    [s.extract() for s in target_soup('style')]

    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

    input_text = target_soup.get_text()
    input_text = strRange(input_text)

    # google natural language api
    headers_gnl = {
        'Content-Type': 'application/json; charset=utf-8'
    }
    target_data_gnl = "{  \"document\":{ \"type\": \"PLAIN_TEXT\", \"content\":\""+input_text+"\"  }"+"}"
    target_response_entities = requests.post('https://language.googleapis.com/v1/documents:analyzeEntities?fields=entities%2Clanguage&key='+GOOGLE_API_KEY, headers=headers_gnl, data=target_data_gnl.encode('utf-8'))
    target_response_categories= requests.post('https://language.googleapis.com/v1/documents:classifyText?key='+GOOGLE_API_KEY, headers=headers_gnl, data=target_data_gnl.encode('utf-8'))
    
    target_ret_response_entities = json.loads(target_response_entities.text)
    target_ret_response_entities['entities'] = dictEntityRange(target_ret_response_entities['entities'])
    target_ret_response_categories = json.loads(target_response_categories.text)

    tag_entities = map(convertTag,target_ret_response_entities['entities'])

    input_dom_target_text = createDomEntity(input_text,tag_entities)

    competitors_text = []
    competitors_ret_response_entities = []
    competitors_ret_response_categories = []

    for key,competitor_link in enumerate(competitor_links):
        # html parse

        competitor_html = requests.get(competitor_link)

        competitor_soup = BeautifulSoup(competitor_html.text, 'html.parser')
        [s.extract() for s in competitor_soup('img')]
        [s.extract() for s in competitor_soup('script')]
        [s.extract() for s in competitor_soup('style')]

        GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        
        # google natural language api
        headers_gnl = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        competitor_soup_text = competitor_soup.get_text()
        competitor_soup_text = strRange(competitor_soup_text)
        competitors_text.append(competitor_soup_text)

        competitor_data_gnl = "{  \"document\":{ \"type\": \"PLAIN_TEXT\", \"content\":\""+competitor_soup_text+"\"  }"+"}"
        competitor_response_entities = requests.post('https://language.googleapis.com/v1/documents:analyzeEntities?fields=entities%2Clanguage&key='+GOOGLE_API_KEY, headers=headers_gnl, data=competitor_data_gnl.encode('utf-8'))
        competitor_response_categories= requests.post('https://language.googleapis.com/v1/documents:classifyText?key='+GOOGLE_API_KEY, headers=headers_gnl, data=competitor_data_gnl.encode('utf-8'))
        competitor_ret_response_entities = json.loads(competitor_response_entities.text)
        competitors_ret_response_entities.append(competitor_ret_response_entities)
        competitor_ret_response_categories = json.loads(competitor_response_categories.text)
        competitors_ret_response_categories.append(competitor_ret_response_categories)

        #Common Category Check
        common_categories = {}

        common_target_ret_response_categories = target_ret_response_categories['categories'][0]['name'].split('/')[1:]

        for category in common_target_ret_response_categories:
            common_categories[category] = 0

        for competitors_categories in competitors_ret_response_categories:
            categories = competitors_categories['categories'][0]['name'].split('/')[1:]
            for category in categories:
                if category in common_categories:
                    common_categories[category] += 1 

        #Common Entity Type and Entity Check
        common_entities = {}
        common_entitytypes = {}
        common_target_entitytypes = {}
        common_target_entites = {}
        for entity in target_ret_response_entities['entities']:
            common_target_entites[entity['name']] = entity['name']
            common_target_entitytypes[entity['type']] = entity['type']
            
        common_com_entitytypes = {}
        common_com_entites = {}
        for i in range(len(competitors_ret_response_entities)):
            common_com_entites[i] = {}
            common_com_entitytypes[i] = {}
            for entity in competitors_ret_response_entities[i]['entities']:
                common_com_entites[i][entity['name']]= entity['name']
                common_com_entitytypes[i][entity['type']]= entity['type']

        for key in common_target_entitytypes:
            common_entitytypes[key] = 0
            
        for key in range(len(common_com_entitytypes)):
            for entitytype in common_com_entitytypes[key]:
                if entitytype in common_target_entitytypes:
                    common_entitytypes[entitytype] += 1 

        for key in common_target_entites:
            common_entities[key] = 0
            
        for key in range(len(common_com_entites)):
            for entity in common_com_entites[key]:
                if entity in common_target_entites:
                    common_entities[entity] += 1                 

        common_entitytypes_data = {}
        common_entities_data = {}

        for key in common_entitytypes:
            if common_entitytypes[key] == 0:
                continue
            common_entitytypes_data[key] = common_entitytypes[key] 

        for key in common_entities:
            if common_entities[key] == 0:
                continue
            common_entities_data[key] = common_entities[key]

        common_entities_array = []
        common_entitytypes_array = []
        common_categories_array = []
        
        for key in common_entities_data:
            temp = [key,common_entities_data[key]]
            common_entities_array.append(temp)
        for key in common_entitytypes_data:
            temp = [key,common_entitytypes_data[key]]
            common_entitytypes_array.append(temp)
        for key in common_categories:
            temp = [key,common_categories[key]]
            common_categories_array.append(temp)

    input_dom_compeditor_texts = []
    for i, competitor_text in enumerate(competitors_text):
        tag_entities = map(convertTag,competitors_ret_response_entities[i]['entities'])
        input_dom_compeditor_text = createDomEntity(competitor_text,tag_entities)
        input_dom_compeditor_texts.append(input_dom_compeditor_text)

    return render_template('index.html',
        target_link=target_link,
        competitor_links=enumerate(competitor_links),
        input_dom_target_text=input_dom_target_text,
        target_text=target_soup.get_text(),
        target_ret_response_entities=enumerate(target_ret_response_entities['entities']),
        target_ret_response_categories=target_ret_response_categories,
        competitors_ret_response_entities=competitors_ret_response_entities,
        competitors_ret_response_categories=competitors_ret_response_categories,
        competitors_text=competitors_text,
        input_dom_compeditor_texts=input_dom_compeditor_texts,
        common_entities_array=common_entities_array,
        common_entitytypes_array=common_entitytypes_array,
        common_categories_array=common_categories_array,
        )

if __name__ == '__main__':
    app.run(debug=True)


