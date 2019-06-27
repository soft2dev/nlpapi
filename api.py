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

    [s.extract() for s in soup('img')]
    [s.extract() for s in soup('script')]
    [s.extract() for s in soup('style')]

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
    response_entities= dictEntityRange(response_entities.get('entities', []))
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
        "categories": categories.get('categories', [])
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

    common_entities_array = []
    common_entitytypes_array = []
    common_categories_array = []

    #Common Entity Type and Entity Check
    common_entities = {}
    common_entitytypes = {}
    common_target_entitytypes = {}
    common_target_entites = {}
    if target_nlp_result['entities']:
        for entity in target_nlp_result['entities']:
            common_target_entites[entity['name']] = entity['name']
            common_target_entitytypes[entity['type']] = entity['type']

        common_com_entitytypes = {}
        common_com_entites = {}
        if len(competitors_nlp_result):
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
            common_categories_data = {}

            #Common Category Check
            common_categories = {}
            if(target_nlp_result['categories']):
                common_target_ret_response_categories = target_nlp_result['categories'][0]['name'].split('/')[1:]

                for category in common_target_ret_response_categories:
                    common_categories[category] = 0

                for competitors_categories in competitors_nlp_result:
                    if(competitors_categories['categories']):
                        categories = competitors_categories['categories'][0]['name'].split('/')[1:]
                        for category in categories:
                            if category in common_categories:
                                common_categories[category] += 1 

            for key in common_entitytypes:
                if common_entitytypes[key] == 0:
                    continue
                common_entitytypes_data[key] = common_entitytypes[key] 

            for key in common_entities:
                if common_entities[key] == 0:
                    continue
                common_entities_data[key] = common_entities[key]

            for key in common_categories:
                if common_categories[key] == 0:
                    continue
                common_categories_data[key] = common_entities[key]
            

    data_lengthes = []
    data_lengthes.append(len(common_entities_data))
    data_lengthes.append(len(common_entitytypes_data))
    data_lengthes.append(len(common_categories))
    data_lengthes.sort(reverse = True)
    
    for key in common_entities_data:
        temp = [key,common_entities_data[key]]
        common_entities_array.append(temp)
    for key in common_entitytypes_data:
        temp = [key,common_entitytypes_data[key]]
        common_entitytypes_array.append(temp)
    for key in common_categories_data:
        temp = [key,common_categories_data[key]]
        common_categories_array.append(temp)

    return {
        'common_max_number':data_lengthes[0],
        'common_entities_array':common_entities_array,
        'common_entitytypes_array':common_entitytypes_array,
        'common_categories_array':common_categories_array
    }
@app.route('/')
def sendGoogle():
    target_link = 'https://barkpost.com/dog-lover-dog-parent'
    competitor_links = [
        'https://www.wideopenpets.com/weird-things-dog-lovers/',
        'https://www.countryliving.com/shopping/gifts/g1478/gifts-for-dog-lovers/'
    ]

    # html parse
    target_html = requests.get(target_link)
    
    target_soup = BeautifulSoup(target_html.text, 'html.parser')
  
    target_nlp_result = get_entities_and_categories_with_googlenlp(target_soup)

    competitors_nlp_result = []
    for key, competitor_link in enumerate(competitor_links):
        # html parse
        competitor_html = requests.get(competitor_link)
        competitor_soup = BeautifulSoup(competitor_html.text, 'html.parser')
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


