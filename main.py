from fastapi import FastAPI
from typing import Optional

app = FastAPI()

@app.get('/blog')
def index(limit=10,published:bool=True,sort:Optional[str] = None):
    # only get 10 published blog
    if published:
        return {'data':limit + ' blog from the db'}
    else:
        return {'data':limit + 'unpublished blog from the db'}

@app.get('/blog/unpublished')
def unpublished():
    return {'data':'all unpublished blog'}

@app.get('/blog/{id}')
def show(id:int):
    return {'data':id}

@app.get('/blog/{id}/comments')
def comments(id):
    return {'data':{'1','2'}}