from fastapi import FastAPI 
from pydantic import BaseModel
app = FastAPI ()
class User (BaseModel) :
  id:int
  name: str
  email:str
  password:str
  friends: int 

class Product (BaseModel):
   id:int
   description:str
   price:int
   quentity:int
   provider:str 

produits = []

@app.post ("/products")
async def add_prod (produit:Product ):
    produits.append (produit)
    return {"new product:",produit.description}

@app.get("/products")
async def show_product ():
   return produits
