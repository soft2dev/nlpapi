# -*- coding: utf-8 -*-

from flask import Flask, jsonify, request,render_template,json
from bs4 import BeautifulSoup
from jinja2 import Template
from dotenv import load_dotenv

import requests
import os

APP_ROOT = os.path.join(os.path.dirname(__file__), '..')   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
TEXTRAZOR_API_KEY = os.getenv('TEXTRAZOR_API_KEY')

app = Flask(__name__) 

def strRange(input_text):
    seperator = u' ' 
    input_text = seperator.join(input_text.split())
    return input_text
def dictEntityRange(dictEntity):
    return sorted(dictEntity, key = lambda entity: entity['name'],reverse=True)
# def get_entities_and_categories_with_googlenlp(soup): return value type
# {
#     "entities": [
#         {
#             'name': 'world',
#             'wiki_url': '',
#             'salience': '2.1359565e-05',
#             'type': 'LOCATION',
#         }
#         ...
#         ...
#     ],
#     "categories":[
#         {
#           "confidence": 0.99,
#           "name": "/People & Society/Family & Relationships/Family"
#         }
#     ]
# }


def get_entities_and_categories_with_googlenlp(soup):

    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    input_text = soup.get_text()
    input_text = strRange(input_text)

    # google natural language api
    headers_gnl = {
        'Content-Type': 'application/json; charset=utf-8'
    }

    target_data_gnl = u"{  \"document\":{ \"type\": \"PLAIN_TEXT\", \"content\":\""+input_text+"\"  }"+"}"
    entities = requests.post('https://language.googleapis.com/v1/documents:analyzeEntities?fields=entities%2Clanguage&key='+GOOGLE_API_KEY, headers=headers_gnl, data=target_data_gnl.encode('utf-8'))
    categories= requests.post('https://language.googleapis.com/v1/documents:classifyText?key='+GOOGLE_API_KEY, headers=headers_gnl, data=target_data_gnl.encode('utf-8'))
    response_entities = json.loads(entities.text)
    response_entities= dictEntityRange(response_entities['entities'])
    categories = json.loads(categories.text)
    new_entities = []
    
    for entity in response_entities:
        find_entity = False 
        wiki_url = ''
        if entity['metadata']:
            if 'wikipedia_url' in entity['metadata'].keys():
                wiki_url = entity['metadata']['wikipedia_url']
        for new_entity in new_entities:
            if(new_entity['name'] == entity['name']):
                find_entity = True
                break
        if  find_entity:
            continue
        new_entities.append({
            'name': entity['name'],
            'wiki_url': wiki_url,
            'salience': entity['salience'],
            'type': entity['type'],
        })
    return {
        "entities": new_entities,
        "categories": categories['categories']
    }

# def get_entities_and_categories_with_googlenlp(soup): return value type
    # {
    #     'common_entities_array':[
    #         ['entity_key','key_value'],
    #         ...
    #         ...
    #         ...
    #     ],
    #     'common_entitytypes_array':[
    #         ['entitytype_key','key_value'],
    #         ...
    #         ...
    #         ...
    #     ],
    #     'common_categories_array':[
    #         ['category_key','key_value'],
    #         ...
    #         ...
    #         ...
    #     ],
    # }
def get_commons(target_nlp_result,competitors_nlp_result):

    #Common Category Check
    common_categories = {}
    common_target_ret_response_categories = target_nlp_result['categories'][0]['name'].split('/')[1:]

    for category in common_target_ret_response_categories:
        common_categories[category] = 0

    for competitors_categories in competitors_nlp_result:
        categories = competitors_categories['categories'][0]['name'].split('/')[1:]
        for category in categories:
            if category in common_categories:
                common_categories[category] += 1 
  
    #Common Entity Type and Entity Check
    common_entities = {}
    common_entitytypes = {}
    common_target_entitytypes = {}
    common_target_entites = {}
    for entity in target_nlp_result['entities']:
        common_target_entites[entity['name']] = entity['name']
        common_target_entitytypes[entity['type']] = entity['type']

    common_com_entitytypes = {}
    common_com_entites = {}
    for i in range(len(competitors_nlp_result)):
        common_com_entites[i] = {}
        common_com_entitytypes[i] = {}
        for entity in competitors_nlp_result[i]['entities']:
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

    return {
        'common_entities_array':common_entities_array,
        'common_entitytypes_array':common_entitytypes_array,
        'common_categories_array':common_categories_array
    }
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

    target_nlp_result = get_entities_and_categories_with_googlenlp(target_soup)

    competitors_nlp_result = []
    for key, competitor_link in enumerate(competitor_links):
        # html parse
        competitor_html = requests.get(competitor_link)
        competitor_soup = BeautifulSoup(competitor_html.text, 'html.parser')
        [s.extract() for s in competitor_soup('img')]
        [s.extract() for s in competitor_soup('script')]
        [s.extract() for s in competitor_soup('style')]
        competitor_nlp_result = get_entities_and_categories_with_googlenlp(competitor_soup)
        competitors_nlp_result.append(competitor_nlp_result)

    commons = get_commons(target_nlp_result,competitors_nlp_result)
    
    return render_template('index.html',
        target_link = target_link,
        competitor_links = enumerate(competitor_links),
        target_nlp_result = target_nlp_result,
        competitors_nlp_result = competitors_nlp_result,
        commons = commons,        
        )

if __name__ == '__main__':
    app.run(debug=True)


