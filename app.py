#!/usr/bin/env python3

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

import openai
import numpy as np

from pgvector.psycopg2 import register_vector
from flask import Flask, jsonify, render_template, request

PG_DB = 'postgres'
PG_USER = 'postgres'
PG_PASSWORD = 'password'
PG_HOST = '127.0.0.1'
PG_PORT = 5432

EMBEDDING_MODEL = 'text-embedding-ada-002'
GPT_MODEL = 'gpt-3.5-turbo-16k'

PROMPT_WITHOUT_EMBEDDING = '''
You are an insurance broker.

Always answer questions in the language of the questioner.
'''

PROMPT_WITH_EMBEDDING = '''
You are an insurance broker.

Always answer questions in the language of the questioner.

Please refer to the following to answer the questions:

"""
%s
"""
'''

openai.api_key = 'your-api-key'

app = Flask(__name__)


def create_embedding(s: str) -> np.array:
    resp = openai.Embedding.create(
        input=s, model=EMBEDDING_MODEL)
    return np.array(resp['data'][0]['embedding'])


def load_docs():
    pwd = os.path.split(os.path.abspath(__file__))[0]
    docs = os.path.join(pwd, 'docs')
    print(f'set doc dir: {docs}')
    for file in os.listdir(docs):
        if not file.endswith('.md'):
            continue
        name = file[:-3]
        if db_exist_by_name(name):
            print(f'doc already exist.')
            continue
        print(f'load doc {name}...')
        with open(os.path.join(docs, file), 'r', encoding='utf-8') as f:
            content = f.read()
            print(f'create embedding for {name}...')
            embedding = create_embedding(content)
            doc = dict(name=name, content=content,
                       embedding=embedding)
            db_insert(doc)
            print(f'doc {name} created.')


def db_conn():
    conn = psycopg2.connect(
        user=PG_USER, password=PG_PASSWORD, database=PG_DB, host=PG_HOST, port=PG_PORT)
    register_vector(conn)
    return conn


def db_insert(doc: dict):
    sql = 'INSERT INTO docs (name, content, embedding) VALUES (%s, %s, %s) RETURNING id'
    with db_conn() as conn:
        cursor = conn.cursor()
        values = (doc['name'], doc['content'], doc['embedding'])
        cursor.execute(sql, values)
        doc['id'] = cursor.fetchone()[0]
        conn.commit()
        cursor.close()


def db_exist_by_name(name: str):
    sql = 'SELECT id FROM docs WHERE name = %s'
    with db_conn() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        values = (name, )
        cursor.execute(sql, values)
        results = cursor.fetchall()
        cursor.close()
        return len(results) > 0


def db_select_all():
    sql = 'SELECT id, name, content FROM docs ORDER BY id'
    with db_conn() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        return results


def db_select_by_embedding(embedding: np.array):
    sql = 'SELECT id, name, content, embedding <=> %s AS distance FROM docs ORDER BY embedding <=> %s LIMIT 3'
    with db_conn() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        values = (embedding, embedding)
        cursor.execute(sql, values)
        results = cursor.fetchall()
        cursor.close()
        return results


@app.route('/')
def index():
    return render_template('index.html', docs=db_select_all())


@app.route('/ask', methods=['POST'])
def ask():
    req = request.get_json(force=True)
    content = req['content']
    print(f'>>>\n{content}\n>>>')
    embedding = create_embedding(content)
    docs = db_select_by_embedding(embedding)
    if len(docs) >= 1 and docs[0]['distance'] < 0.5:
        messages = [dict(role='system', content=PROMPT_WITH_EMBEDDING % docs[0]['content']),
                    dict(role='user', content=content)]
    else:
        print(f'no related documents found.')
        messages = [dict(role='system', content=PROMPT_WITHOUT_EMBEDDING),
                    dict(role='user', content=content)]
    resp = openai.ChatCompletion.create(
        messages=messages, model=GPT_MODEL, temperature=0)
    print(f'<<<\n{resp}\n<<<')
    if 'error' in resp:
        return jsonify({
            'error': resp['error']
        })
    answer = resp['choices'][0]['message']['content']
    return jsonify({
        'message': resp['choices'][0]['message']
    })


if __name__ == '__main__':
    load_docs()
    app.run(host='0.0.0.0', port=5000, debug=True)
