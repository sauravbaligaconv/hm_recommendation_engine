from flask import Flask,request,redirect,url_for,jsonify,make_response
from flask import render_template
import pandas as pd
from numpy.testing import assert_almost_equal
import numpy as np
from ast import literal_eval
import time
import win32com.client as client
import pythoncom
import os
import random
import itertools
from itertools import chain
import string
import random
from flask_sqlalchemy import Pagination
from difflib import SequenceMatcher
#import pathlib
app = Flask(__name__)  #Initializing the Flask Instance
#Global Variables
cart_id_1=[] #used to store articles added to cart
time_global=[] #used to store time spent on a product or a category
clicked=[] #used to store the item or category the user viewed
cust_id_logged_in=[] #the logged in customer
added_to_cart_and_removed=[] #the articles that where added to cart and then removed
swipe_details=[] #Details whether the image was right swipped or left swipped
images_for_swipe=[]  #Details of the 5 images that were present in the images in the swipe game 
search_details=[] #Store the details of the products the customer searched
scratch_card_coupon=[]  # code of the Scratch card coupon won by the customer
#embeds=pd.read_csv('static/data/similarities.csv')
df=pd.read_csv('static/data/1_sim.csv')  #Importing Image similarity data in chuncks of 1000
for i in range(2,6):
    df1=pd.read_csv('static/data/{}_sim.csv'.format(i))
    final=pd.concat([df,df1],axis=0)
    df=final
    print(df.shape)
embeds=df
embeds=embeds.set_index('path')
images=pd.read_csv('static/data/img_pres.csv') # Image dataset
images=images.drop('Unnamed: 0',axis=1)
images.rename(columns={'0':'img_id'},inplace=True)
images['ids']=images['img_id'].apply(lambda x:x[1:10])
images['path']=images['img_id'].apply(lambda x: f"images/{x[0:3]}/{x}")
ids=images['ids'][0:5000]
ids=[int(x) for x in ids]
item_similarities1=pd.read_csv('static/data/content_based_similar_items.csv',converters={'similar_items': literal_eval})#content based similarity data
item_similarities1.drop('Unnamed: 0',axis=1,inplace=True)
articles=pd.read_csv('static/data/articles.csv')
article1=articles.copy()
articles=articles.loc[articles['article_id'].isin(ids)][['article_id','product_code', 'prod_name', 'product_type_no', 'product_type_name',
       'product_group_name', 'graphical_appearance_no',
       'graphical_appearance_name', 'colour_group_code', 'colour_group_name',
       'perceived_colour_value_id', 'perceived_colour_value_name',
       'perceived_colour_master_id', 'perceived_colour_master_name',
       'department_no', 'department_name', 'index_code', 'index_name',
       'index_group_no', 'index_group_name', 'section_no', 'section_name',
       'garment_group_no', 'garment_group_name', 'detail_desc']]
print('waiting for transactions next')
#transactions=pd.read_csv('static/data/transactions_train.csv')
df=pd.read_csv('static/data/1.csv') #importing transactions data in chunks
for i in range(2,39):
    df1=pd.read_csv('static/data/{}.csv'.format(i))
    final=pd.concat([df,df1],axis=0)
    df=final
    print(df.shape)
transactions=df
unique_cust_id=transactions.customer_id.unique()
test_data1=transactions.groupby(by="customer_id")['article_id'].agg(list).reset_index()
transactions=transactions.loc[transactions['article_id'].isin(ids)][[ 'customer_id', 'article_id', 'price']]
print('transactions done')
test_data = transactions.groupby(by="customer_id")['article_id'].agg(list).reset_index()
print('test done')
customers_final=test_data['customer_id']
print('item_sim start')
item_similarities = pd.read_csv('static/data/item_similarities.csv')
item_similarities.drop('Unnamed: 0',axis=1,inplace=True)
print('import done')
print('calling function')
price_details=pd.read_csv('static/data/price_details.csv')
print('price details done')
products=list(articles['product_type_name'].unique())   ###make changes here. bcz this is set on image based so only 5000 images
products1=list(article1['product_type_name'].unique())
#print('home   :',products)
item='shirt'
path_store=[]  #used to store path of the image
price=[]    #used to  store price of the image
prod_name=[] #used to store product name
desc=[] #used to store description
for i in products:
    if str(item) in i.lower().strip():
        articles_list=articles[articles['product_type_name']==i]['article_id'].to_list()
        trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
        trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
        trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
        trans_arts=trans_arts.sort_values('counts',ascending=False).head(200)
        rows=2
        for num, x in enumerate(trans_arts['article_id']):
            a=str(x)
            p=price_details[price_details['article_id']==int(a)]['price'].values
            pn=price_details[price_details['article_id']==int(a)]['prod_name'].values
            d=price_details[price_details['article_id']==int(a)]['detail_desc'].values
            path=f"/static/images/0{a[0:2]}/0{a}.jpg"
            path_store.append(path)
            price.append(np.round(((np.round(p[0]*100000)/10)*10)/10)*10)
            prod_name.append(pn[0])
            desc.append(d[0])
#print('shirts product name:',prod_name)
#print('loading the images')
#print(path_store[10])
#images1=[]
#for file in path_store:
#       with open(file, "rb") as image:
#            encoded = base64.b64encode(image.read()).decode()
#            images1.append(f"data:image/jpeg;base64,{encoded}")



#Retreive most similar images
def retrieve_most_similar_products(idd):
    a=articles[articles['article_id']==idd].index.values.astype('int')
    #print('article purchased:',idd,articles.loc[a,'product_type_name'].item())
    input_product=price_details[price_details['article_id']==idd]['prod_name'].values
    input_price=price_details[price_details['article_id']==idd]['price'].values
    input_det=price_details[price_details['article_id']==idd]['detail_desc'].values
    a='0'+str(idd)+'.jpg'
    b=images[images['img_id']==a].index.values.astype('int')
    given_img=images.loc[images['img_id']==a]['path'].item()
    closest_imgs = embeds[given_img].sort_values(ascending=False)[1:4+1].index.values
    price=[]
    prod_name=[]
    desc=[]
    for i in range(len(closest_imgs)):
        p=price_details[price_details['article_id']==int(closest_imgs[i][12:21])]['price'].values
        price.append(np.round(((np.round(p[0]*100000)/10)*10)/10)*10)
        pname=price_details[price_details['article_id']==int(closest_imgs[i][12:21])]['prod_name'].values
        prod_name.append(pname[0])
        d=price_details[price_details['article_id']==int(closest_imgs[i][12:21])]['detail_desc'].values
        desc.append(d[0])
    return list(zip(closest_imgs,price,prod_name,desc)),input_product[0],np.round(((np.round(input_price[0]*100000)/10)*10)/10)*10,input_det[0]

#Most Similar Personalised product
def retrieve_most_similar_personalised_products(idd):
    a=article1[article1['article_id']==idd].index.values.astype('int')
    #print('article purchased:',idd,articles.loc[a,'product_type_name'].item())
    input_product=price_details[price_details['article_id']==idd]['prod_name'].values
    input_price=price_details[price_details['article_id']==idd]['price'].values
    input_det=price_details[price_details['article_id']==idd]['detail_desc'].values
    img_path=[]
    similar_items=item_similarities1[item_similarities1['item']==int(idd)]['similar_items'].values[0]
    print(similar_items)
    for i,x in enumerate(similar_items):
        id = str(x)
        path = f"images/0{id[0:2]}/0{id}.jpg"
        img_path.append(path)
    price_r_item=[]
    prod_name_r_item=[]
    desc_r_item=[]
    for i in similar_items:
        price_r=price_details[price_details['article_id']==int(i)]['price'].values
        price_r_item.append(np.round(((np.round(price_r[0]*100000)/10)*10)/10)*10)
        prod_name_r=price_details[price_details['article_id']==int(i)]['prod_name'].values
        prod_name_r_item.append(prod_name_r[0])
        desc_r=price_details[price_details['article_id']==int(i)]['detail_desc'].values
        desc_r_item.append(desc_r[0])
    print(price_r_item)
    print(prod_name_r_item)
    print(desc_r_item)
    det_p_rec=list(zip(img_path,price_r_item,prod_name_r_item,desc_r_item))
    return det_p_rec,input_product[0],np.round(((np.round(input_price[0]*100000)/10)*10)/10)*10,input_det[0]


global numRec
numRec = 4
def getNames(inputName, similarNames, similarValues):
    images = list(similarNames.loc[inputName, :])
    values = list(similarValues.loc[inputName, :])
    if inputName in images:
        assert_almost_equal(max(values), 1, decimal = 5)
        images.remove(inputName)
        values.remove(max(values))
    return inputName, images[0:numRec], values[0:numRec]

def getImages(inputImage):
    return 1

#Login Page
@app.route("/",methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        print(request.form['username'])
        if request.form['username'] in unique_cust_id:
            cust_id_logged_in.append(request.form['username'])
            print('will be allowed to enter')
            return redirect(url_for('home'))
    return render_template('index.html')


#home page
@app.route("/home",methods=['GET', 'POST'])
# Need to write a function that is called when opening the site

def home():
    #print(images)
    start=time.time()   #start time
    time_global.append(start) 
    if('Log In' in clicked):
        clicked.append('Home')
    else:
        clicked.append('Log In')
    page=request.args.get('page',1,type=int)
    det=list(zip(path_store,price,prod_name,desc))
    start = (page - 1) * 20
    end = start + 20
    items = det[start:end]
    #print(items)
    pagination = Pagination(None, page, 20, len(det), items)
    #print(pagination)
    print('items',pagination.items)
    print('has prev',pagination.has_prev)
    print('pages',pagination.pages)
    print('iter_pages',pagination.iter_pages)
    if(page>=pagination.pages):
        page=1
    return render_template('home.html', images = pagination,pages=page)

#when an image is clicked on the home page this function gets triggered. we store the clicked detail and provide relevant recommendation
@app.route("/recommend")
def recommend():
    start=time.time()
    time_global.append(start)
    selectedImage = request.args.get('selectedImage')
    b=selectedImage[7:]
    selectedImage1=int(selectedImage[-13:-4])
    clicked.append(selectedImage1)
    print('rec',selectedImage1)
    details,input_product,input_price,input_det=retrieve_most_similar_products(selectedImage1)
    first_random=np.random.choice(ids,8)
    second_random=np.random.choice(ids,8)
    first=[]
    first_product_list=[]
    first_det_list=[]
    first_price_list=[]
    second=[]
    second_product_list=[]
    second_det_list=[]
    second_price_list=[]
    for i in first_random:
        a=str(i)
        path=f"/images/0{a[0:2]}/0{a}.jpg"
        first.append(path)
        first_product=price_details[price_details['article_id']==i]['prod_name'].values
        first_product_list.append(first_product[0])
        first_price=price_details[price_details['article_id']==i]['price'].values
        first_price_list.append(np.round(((np.round(first_price[0]*100000)/10)*10)/10)*10)
        first_det=price_details[price_details['article_id']==i]['detail_desc'].values
        first_det_list.append(first_det[0])
    details_first=list(zip(first,first_product_list,first_det_list,first_price_list))
    for i in second_random:
        a=str(i)
        path=f"/images/0{a[0:2]}/0{a}.jpg"
        second.append(path)
        second_product=price_details[price_details['article_id']==i]['prod_name'].values
        second_product_list.append(second_product[0])
        second_price=price_details[price_details['article_id']==i]['price'].values
        second_price_list.append(np.round(((np.round(second_price[0]*100000)/10)*10)/10)*10)
        second_det=price_details[price_details['article_id']==i]['detail_desc'].values
        second_det_list.append(second_det[0])
    details_second=list(zip(second,second_product_list,second_det_list,second_price_list))
    return render_template('recommend.html',input_image=b,details=details,input_product=input_product,input_price=input_price,input_det=input_det,details_first=details_first,details_second=details_second)



#Same as previous function but with the slight change in recording the clicks.To solve issues with selectedImage variables it is set as a different function 
@app.route("/recommend1")
def recommend1():
    start=time.time()
    time_global.append(start)
    selectedImage = request.args.get('selectedImage')
    selectedImage1=int(selectedImage[-13:-4])
    clicked.append(selectedImage1)
    print('rec1',selectedImage1)
    print('clicked',clicked)
    print(time_global)
    details,input_product,input_price,input_det=retrieve_most_similar_products(selectedImage1)
    first_random=np.random.choice(ids,8)
    second_random=np.random.choice(ids,8)
    first=[]
    first_product_list=[]
    first_det_list=[]
    first_price_list=[]
    second=[]
    second_product_list=[]
    second_det_list=[]
    second_price_list=[]
    for i in first_random:
        a=str(i)
        path=f"/images/0{a[0:2]}/0{a}.jpg"
        first.append(path)
        first_product=price_details[price_details['article_id']==i]['prod_name'].values
        first_product_list.append(first_product[0])
        first_price=price_details[price_details['article_id']==i]['price'].values
        first_price_list.append(np.round(((np.round(first_price[0]*100000)/10)*10)/10)*10)
        first_det=price_details[price_details['article_id']==i]['detail_desc'].values
        first_det_list.append(first_det[0])
    details_first=list(zip(first,first_product_list,first_det_list,first_price_list))
    for i in second_random:
        a=str(i)
        path=f"/images/0{a[0:2]}/0{a}.jpg"
        second.append(path)
        second_product=price_details[price_details['article_id']==i]['prod_name'].values
        second_product_list.append(second_product[0])
        second_price=price_details[price_details['article_id']==i]['price'].values
        second_price_list.append(np.round(((np.round(second_price[0]*100000)/10)*10)/10)*10)
        second_det=price_details[price_details['article_id']==i]['detail_desc'].values
        second_det_list.append(second_det[0])
    details_second=list(zip(second,second_product_list,second_det_list,second_price_list))
    return render_template('recommend.html',input_image=selectedImage,details=details,input_product=input_product,input_price=input_price,input_det=input_det,details_first=details_first,details_second=details_second)


#Add to cart
@app.route('/quick_add')
def quick_add():
    selectedImage = request.args.get('filename')
    id=selectedImage[-13:-4]
    cart_id_1.append(id)  #product id added to cart_id_1 list
    print(cart_id_1)
    det=list(zip(path_store,price,prod_name,desc))
    return render_template('home.html',images=det)


#Checking the cart 
@app.route('/cart')
def check_cart():
    start=time.time()
    time_global.append(start)
    clicked.append('checking cart')
    img_name=[]
    price_cart=[]
    product_name_cart=[]
    for i in cart_id_1:
        pd=price_details[price_details['article_id']==int(i)]['price'].values
        price_cart.append(np.round(((np.round(pd[0]*100000)/10)*10)/10)*10)
        pname=price_details[price_details['article_id']==int(i)]['prod_name'].values
        product_name_cart.append(pname[0])
        path=f"/static/images/0{i[0:2]}/0{i}.jpg"
        img_name.append(path)
    print(sum(price_cart))
    print(img_name)
    cart_details_final=list(zip(product_name_cart,price_cart,img_name))
    return render_template('cart.html',ab=cart_details_final,total_price=sum(price_cart))

#Categorical product filtering. Here checking the category of Menswear
@app.route('/Menswear')
def menswear():
    item1='menswear'
    start=time.time()
    time_global.append(start)
    selectedcat = request.args.get('selected_cat')
    print(item1)
    print(selectedcat)
    if selectedcat==None:
        clicked.append('Mens-Wear')
    else:
        clicked.append(selectedcat)
    path_store_shirt=[]
    price_shirt=[]
    prod_name_shirt=[]
    desc_shirt=[]
    print('inside shirt:')
    mens=articles.index_group_name.unique()                    
    mens_sections=articles[articles.index_group_name=='Menswear'].section_name.unique()
    print(mens)
    print(mens_sections)
    if selectedcat==None:
        print('entered none condition')
        
        articles_list=articles[(articles['index_group_name']=='Menswear')]['article_id'].to_list()
        trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
        trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
        trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
        trans_arts=trans_arts.sort_values('counts',ascending=False).head(24)
        rows=2
        for num, x in enumerate(trans_arts['article_id']):
            a=str(x)
            p=price_details[price_details['article_id']==int(a)]['price'].values
            pn=price_details[price_details['article_id']==int(a)]['prod_name'].values
            d=price_details[price_details['article_id']==int(a)]['detail_desc'].values
            path=f"/static/images/0{a[0:2]}/0{a}.jpg"
            path_store_shirt.append(path)
            price_shirt.append(np.round(((np.round(p[0]*100000)/10)*10)/10)*10)
            prod_name_shirt.append(pn[0])
            desc_shirt.append(d[0])
    else:
        print('entered the change condition')
        articles_list=articles[(articles['index_group_name']=='Menswear')&(articles['section_name']==selectedcat)]['article_id'].to_list()
        trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
        trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
        trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
        trans_arts=trans_arts.sort_values('counts',ascending=False).head(24)
        rows=2
        for num, x in enumerate(trans_arts['article_id']):
            a=str(x)
            p=price_details[price_details['article_id']==int(a)]['price'].values
            pn=price_details[price_details['article_id']==int(a)]['prod_name'].values
            d=price_details[price_details['article_id']==int(a)]['detail_desc'].values
            path=f"/static/images/0{a[0:2]}/0{a}.jpg"
            path_store_shirt.append(path)
            price_shirt.append(np.round(((np.round(p[0]*100000)/10)*10)/10)*10)
            prod_name_shirt.append(pn[0])
            desc_shirt.append(d[0])
                
    det_shirt=list(zip(path_store_shirt,price_shirt,prod_name_shirt,desc_shirt))
    page=request.args.get('page',1,type=int)
    start = (page - 1) * 20
    end = start + 20
    items = det_shirt[start:end]
    #print(items)
    pagination = Pagination(None, page, 20, len(det_shirt), items)
    #print(pagination)
    print('pages',pagination.pages)
    if(page>=pagination.pages):
        page=1
    return render_template('home1.html', images = det_shirt ,catg=mens_sections,func='menswear') 


#Categorical product filtering. Here checking the category of Ladieswear
@app.route('/Ladieswear')
def Ladieswear():
    item1='ladieswear'
    start=time.time()
    time_global.append(start)
    selectedcat = request.args.get('selected_cat')
    if selectedcat==None:
        clicked.append('Ladies-wear')
    else:
        clicked.append(selectedcat)
    print(item1)
    print(selectedcat)
    path_store_shirt=[]
    price_shirt=[]
    prod_name_shirt=[]
    desc_shirt=[]
    print('inside ladies shirt:')
    ladies=articles.index_group_name.unique()
    ladies_sections=articles[articles.index_group_name=='Ladieswear'].section_name.unique()
    print(ladies_sections)
    if selectedcat==None:
        print('entered none condition')
        
        articles_list=articles[(articles['index_group_name']=='Ladieswear')]['article_id'].to_list()
        trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
        trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
        trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
        trans_arts=trans_arts.sort_values('counts',ascending=False).head(24)
        rows=2
        for num, x in enumerate(trans_arts['article_id']):
            a=str(x)
            if(len(a)==0):
                continue
            else:
                print(a)
                p=price_details[price_details['article_id']==int(a)]['price'].values
                if(len(p)==0):
                    continue
                pn=price_details[price_details['article_id']==int(a)]['prod_name'].values
                d=price_details[price_details['article_id']==int(a)]['detail_desc'].values
                path=f"/static/images/0{a[0:2]}/0{a}.jpg"
                path_store_shirt.append(path)
                price_shirt.append(np.round(((np.round(p[0]*100000)/10)*10)/10)*10)
                prod_name_shirt.append(pn[0])
                desc_shirt.append(d[0])
    else:
        print('entered the change condition')
        
        articles_list=articles[(articles['index_group_name']=='Ladieswear')&(articles['section_name']==selectedcat)]['article_id'].to_list()
        trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
        trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
        trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
        trans_arts=trans_arts.sort_values('counts',ascending=False).head(24)
        rows=2
        for num, x in enumerate(trans_arts['article_id']):
            a=str(x)
            if(len(a)==0):
                continue
            p=price_details[price_details['article_id']==int(a)]['price'].values
            if(len(p)==0):
                continue
            pn=price_details[price_details['article_id']==int(a)]['prod_name'].values
            d=price_details[price_details['article_id']==int(a)]['detail_desc'].values
            path=f"/static/images/0{a[0:2]}/0{a}.jpg"
            path_store_shirt.append(path)
            price_shirt.append(np.round(((np.round(p[0]*100000)/10)*10)/10)*10)
            prod_name_shirt.append(pn[0])
            desc_shirt.append(d[0])
                
    det_shirt=list(zip(path_store_shirt,price_shirt,prod_name_shirt,desc_shirt))
    print(prod_name_shirt)
    return render_template('home1.html', images = det_shirt,catg=ladies_sections,func='Ladieswear')



#Categorical product filtering. Here checking the category of sport
@app.route('/Sport')
def Sport():
    item1='sport'
    start=time.time()
    time_global.append(start)
    selectedcat = request.args.get('selected_cat')
    print(item1)
    print(selectedcat)
    if selectedcat==None:
        clicked.append('Sports-Wear')
    else:
        clicked.append(selectedcat)

    
    path_store_shirt=[]
    price_shirt=[]
    prod_name_shirt=[]
    desc_shirt=[]
    print('inside sport:')
    sport=articles.index_group_name.unique()
    sport_sections=articles[articles.index_group_name=='Sport'].section_name.unique()
    print(sport_sections)
    sim_ratio=[]
    if selectedcat==None:
        print('entered none condition')
        
        articles_list=articles[(articles['index_group_name']=='Sport')]['article_id'].to_list()
        trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
        trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
        trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
        trans_arts=trans_arts.sort_values('counts',ascending=False).head(24)
        rows=2
        for num, x in enumerate(trans_arts['article_id']):
            a=str(x)
            p=price_details[price_details['article_id']==int(a)]['price'].values
            pn=price_details[price_details['article_id']==int(a)]['prod_name'].values
            d=price_details[price_details['article_id']==int(a)]['detail_desc'].values
            path=f"/static/images/0{a[0:2]}/0{a}.jpg"
            path_store_shirt.append(path)
            price_shirt.append(np.round(((np.round(p[0]*100000)/10)*10)/10)*10)
            prod_name_shirt.append(pn[0])
            desc_shirt.append(d[0])
    else:
        print('entered the change condition')
        for i in sport_sections:
            sim_ratio.append(SequenceMatcher(None, selectedcat, i).ratio())
        print(sim_ratio)
        if(sim_ratio[0]>sim_ratio[1]):
            selectedcat=sport_sections[0]
        else:
            selectedcat=sport_sections[1]
        articles_list=articles[(articles['index_group_name']=='Sport')&(articles['section_name']==selectedcat)]['article_id'].to_list()
        trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
        trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
        trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
        trans_arts=trans_arts.sort_values('counts',ascending=False).head(24)
        rows=2
        for num, x in enumerate(trans_arts['article_id']):
            a=str(x)
            p=price_details[price_details['article_id']==int(a)]['price'].values
            pn=price_details[price_details['article_id']==int(a)]['prod_name'].values
            d=price_details[price_details['article_id']==int(a)]['detail_desc'].values
            path=f"/static/images/0{a[0:2]}/0{a}.jpg"
            path_store_shirt.append(path)
            price_shirt.append(np.round(((np.round(p[0]*100000)/10)*10)/10)*10)
            prod_name_shirt.append(pn[0])
            desc_shirt.append(d[0])
                
    det_shirt=list(zip(path_store_shirt,price_shirt,prod_name_shirt,desc_shirt))
    print(prod_name_shirt)
    return render_template('home1.html', images = det_shirt,catg=sport_sections,func='Sport')

#Categorical product filtering. Here checking the category of baby children
@app.route('/Baby_children')
def Baby_children():
    item1='baby'
    start=time.time()
    time_global.append(start)
    selectedcat = request.args.get('selected_cat')
    if selectedcat==None:
        clicked.append('Baby Section')
    else:
        clicked.append(selectedcat)
    print(item1)
    print(selectedcat)
    path_store_shirt=[]
    price_shirt=[]
    prod_name_shirt=[]
    desc_shirt=[]
    print('inside Baby:')
    mens=articles.index_group_name.unique()
    mens_sections=articles[articles.index_group_name=='Baby/Children'].section_name.unique()
    if selectedcat==None:
        #clicked.append('Baby section')
        print('entered none condition')
        articles_list=articles[(articles['index_group_name']=='Baby/Children')]['article_id'].to_list()
        trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
        trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
        trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
        trans_arts=trans_arts.sort_values('counts',ascending=False).head(24)
        rows=2
        for num, x in enumerate(trans_arts['article_id']):
            a=str(x)
            p=price_details[price_details['article_id']==int(a)]['price'].values
            pn=price_details[price_details['article_id']==int(a)]['prod_name'].values
            d=price_details[price_details['article_id']==int(a)]['detail_desc'].values
            path=f"/static/images/0{a[0:2]}/0{a}.jpg"
            path_store_shirt.append(path)
            price_shirt.append(np.round(((np.round(p[0]*100000)/10)*10)/10)*10)
            prod_name_shirt.append(pn[0])
            desc_shirt.append(d[0])
    else:
        print('entered the change condition')
        articles_list=articles[(articles['index_group_name']=='Baby/Children')&(articles['section_name']==selectedcat)]['article_id'].to_list()
        trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
        trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
        trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
        trans_arts=trans_arts.sort_values('counts',ascending=False).head(24)
        rows=2
        for num, x in enumerate(trans_arts['article_id']):
            a=str(x)
            p=price_details[price_details['article_id']==int(a)]['price'].values
            pn=price_details[price_details['article_id']==int(a)]['prod_name'].values
            d=price_details[price_details['article_id']==int(a)]['detail_desc'].values
            path=f"/static/images/0{a[0:2]}/0{a}.jpg"
            path_store_shirt.append(path)
            price_shirt.append(np.round(((np.round(p[0]*100000)/10)*10)/10)*10)
            prod_name_shirt.append(pn[0])
            desc_shirt.append(d[0])
            
    det_shirt=list(zip(path_store_shirt,price_shirt,prod_name_shirt,desc_shirt))
    print(prod_name_shirt)
    return render_template('home1.html', images = det_shirt,catg=mens_sections,func='Baby_children')


#Game of left and right swipe.Based on recommendation of previous purchases the customer is shown 5 cards which he can right and left swipe and based on the swipes he will get the recommendation    
@app.route('/swipe_personalised')
def swipe_personalised():
    similar_list_swipe=[]
    print('img from swipe',images_for_swipe)
    print(swipe_details)
    for i in range(len(swipe_details[0])):
        if(swipe_details[0][i]>0):
            swipe_details[0][i]='Right'
        else:
            swipe_details[0][i]='Left'
    print(swipe_details[0])
    print(cust_id_logged_in*5)
    swipe_df=pd.DataFrame(columns=['customer_id','images','swipe'])
    swipe_df['customer_id']=cust_id_logged_in*5
    swipe_df['images']=images_for_swipe[0]
    swipe_df['swipe']=swipe_details[0]
    print(swipe_df)
    right_swipes=swipe_df[swipe_df.swipe=='Right']
    print(right_swipes)
    print(right_swipes.images.values)
    for ids in right_swipes.images.values:
        idd = str(ids)
        #print(idd)
        similar_items_swipe = list(item_similarities1[item_similarities1['item']==int(idd)]['similar_items'])[0][1:]
        #print(similar_items_swipe)
        similar_list_swipe.append(similar_items_swipe)
    #print(similar_list_swipe)
    new_sim_list_swipe = itertools.chain(*similar_list_swipe)
    new_sim_list_swipe=list(new_sim_list_swipe)
    #print(new_sim_list_swipe)
    img_path_swipe=[]
    for i,x in enumerate(new_sim_list_swipe):
            id = str(x)
            path = f"/static/images/0{id[0:2]}/0{id}.jpg"
            img_path_swipe.append(path)
    price_r_item=[]
    prod_name_r_item=[]
    desc_r_item=[]
    for i in new_sim_list_swipe:
        #print(i)
        price_r=price_details[price_details['article_id']==int(i)]['price'].values
        if(len(price_r)==0):
            continue
        price_r_item.append(np.round(((np.round(price_r[0]*100000)/10)*10)/10)*10)
        prod_name_r=price_details[price_details['article_id']==int(i)]['prod_name'].values
        prod_name_r_item.append(prod_name_r[0])
        desc_r=price_details[price_details['article_id']==int(i)]['detail_desc'].values
        desc_r_item.append(desc_r[0])
#print(price_r_item)
#print(prod_name_r_item)
#print(desc_r_item)
    det_p_rec=list(zip(img_path_swipe,price_r_item,prod_name_r_item,desc_r_item))
    print(det_p_rec)
    images_for_swipe.clear()
    swipe_details.clear()
    return render_template('home_content_based_swipe.html',images=det_p_rec)


#Personalised Recommendation based on customers purchase history
@app.route('/Personalised_Reccomendation')
def Personalised_Reccomendation():
    #login id should be fed here 
    cust_id=cust_id_logged_in[0]
    print(cust_id)
    start=time.time()
    time_global.append(start)
    clicked.append('checking personalised')
    img_path=[]
    index_pos=test_data1[test_data1['customer_id']==cust_id].index.values
    arts=test_data1.iloc[index_pos[0],1]
    products_1=[]
    items_1=[]
    for a in arts:
        art_index=article1[article1.article_id==a].index.values
        products_1.append(article1.at[art_index[0],'product_type_name'])
        items_1.append(a)
    unique_items=pd.DataFrame()
    unique_items['products']=pd.Series(products_1)
    unique_items['article_ids']=pd.Series(items_1)
    unique_products=unique_items.groupby('products')['article_ids'].agg(list).reset_index()
    final_list=[]
    for i,j in zip(unique_products['products'],unique_products['article_ids']):
        arts_list=[]
        for x in j:
            arts_list.append(str(x))
            for i in arts_list:
                final_list.append(i)
    final_list=set(final_list)
    similar_list=[]
    for ids in final_list:
        idd = str(ids)
        path = f"images/0{idd[0:2]}/0{idd}.jpg"
    #similar_items = list(item_similarities[item_similarities['item']==int(idd)]['similar_items'])[0]
        #similar_items=item_similarities1[item_similarities1['item']==int(idd)]['similar_items'].values[0]
        similar_items = list(item_similarities1[item_similarities1['item']==int(idd)]['similar_items'])[0][1:]
        similar_list.append(similar_items)
    new_sim_list = itertools.chain(*similar_list)
    new_sim_list=list(new_sim_list)
    print(new_sim_list)
    for i,x in enumerate(new_sim_list):
        id = str(x)
        path = f"static/images/0{id[0:2]}/0{id}.jpg"
        img_path.append(path)
    #print(img_path)
    price_r_item=[]
    prod_name_r_item=[]
    desc_r_item=[]
    for i in new_sim_list:
        price_r=price_details[price_details['article_id']==int(i)]['price'].values
        price_r_item.append(np.round(((np.round(price_r[0]*100000)/10)*10)/10)*10)
        prod_name_r=price_details[price_details['article_id']==int(i)]['prod_name'].values
        prod_name_r_item.append(prod_name_r[0])
        desc_r=price_details[price_details['article_id']==int(i)]['detail_desc'].values
        desc_r_item.append(desc_r[0])
#print(price_r_item)
    print(prod_name_r_item)
#print(desc_r_item)
    page=request.args.get('page',1,type=int)
    start = (page - 1) * 20
    end = start + 20
    #print(items)
    det_p_rec=list(zip(img_path,price_r_item,prod_name_r_item,desc_r_item))
    items = det_p_rec[start:end]
    pagination = Pagination(None, page, 20, len(det_p_rec), items)
    if(page>=pagination.pages):
        page=1
    return render_template('home_content_based.html',images=pagination,pages=page)


#This function gets triggered when a image is clicked on the personalised recommendation page and based on that click 5 more similar products are recommended
@app.route('/Personalised')
def recommend_personalised():
    start=time.time()
    time_global.append(start)
    selectedImage = request.args.get('selectedImage')
    b=selectedImage[7:]
    selectedImage1=int(selectedImage[-13:-4])
    clicked.append(selectedImage1)
    print('rec',selectedImage1)
    details,input_product,input_price,input_det=retrieve_most_similar_personalised_products(selectedImage1)
    first_random=np.random.choice(ids,8)
    second_random=np.random.choice(ids,8)
    first=[]
    first_product_list=[]
    first_det_list=[]
    first_price_list=[]
    second=[]
    second_product_list=[]
    second_det_list=[]
    second_price_list=[]
    for i in first_random:
        a=str(i)
        path=f"images/0{a[0:2]}/0{a}.jpg"
        first.append(path)
        first_product=price_details[price_details['article_id']==i]['prod_name'].values
        first_product_list.append(first_product[0])
        first_price=price_details[price_details['article_id']==i]['price'].values
        first_price_list.append(np.round(((np.round(first_price[0]*100000)/10)*10)/10)*10)
        first_det=price_details[price_details['article_id']==i]['detail_desc'].values
        first_det_list.append(first_det[0])
    details_first=list(zip(first,first_product_list,first_det_list,first_price_list))
    for i in second_random:
        a=str(i)
        path=f"/images/0{a[0:2]}/0{a}.jpg"
        second.append(path)
        second_product=price_details[price_details['article_id']==i]['prod_name'].values
        second_product_list.append(second_product[0])
        second_price=price_details[price_details['article_id']==i]['price'].values
        second_price_list.append(np.round(((np.round(second_price[0]*100000)/10)*10)/10)*10)
        second_det=price_details[price_details['article_id']==i]['detail_desc'].values
        second_det_list.append(second_det[0])
    details_second=list(zip(second,second_product_list,second_det_list,second_price_list))
    return render_template('recommend_personalised.html',input_image=b,details=details,input_product=input_product,input_price=input_price,input_det=input_det,details_first=details_first,details_second=details_second)

#same as previous.used to solve issues arising at selectedImage
@app.route('/Personalised1')
def recommend_personalised_1():
    start=time.time()
    time_global.append(start)
    selectedImage = request.args.get('selectedImage')
    b=selectedImage[7:]
    print(b)
    selectedImage1=int(selectedImage[-13:-4])
    clicked.append(selectedImage1)
    print('rec',selectedImage1)
    details,input_product,input_price,input_det=retrieve_most_similar_personalised_products(selectedImage1)
    first_random=np.random.choice(ids,8)
    second_random=np.random.choice(ids,8)
    first=[]
    first_product_list=[]
    first_det_list=[]
    first_price_list=[]
    second=[]
    second_product_list=[]
    second_det_list=[]
    second_price_list=[]
    for i in first_random:
        a=str(i)
        path=f"/images/0{a[0:2]}/0{a}.jpg"
        first.append(path)
        first_product=price_details[price_details['article_id']==i]['prod_name'].values
        first_product_list.append(first_product[0])
        first_price=price_details[price_details['article_id']==i]['price'].values
        first_price_list.append(np.round(((np.round(first_price[0]*100000)/10)*10)/10)*10)
        first_det=price_details[price_details['article_id']==i]['detail_desc'].values
        first_det_list.append(first_det[0])
    details_first=list(zip(first,first_product_list,first_det_list,first_price_list))
    for i in second_random:
        a=str(i)
        path=f"/images/0{a[0:2]}/0{a}.jpg"
        second.append(path)
        second_product=price_details[price_details['article_id']==i]['prod_name'].values
        second_product_list.append(second_product[0])
        second_price=price_details[price_details['article_id']==i]['price'].values
        second_price_list.append(np.round(((np.round(second_price[0]*100000)/10)*10)/10)*10)
        second_det=price_details[price_details['article_id']==i]['detail_desc'].values
        second_det_list.append(second_det[0])
    details_second=list(zip(second,second_product_list,second_det_list,second_price_list))
    return render_template('recommend_personalised.html',input_image=selectedImage,details=details,input_product=input_product,input_price=input_price,input_det=input_det,details_first=details_first,details_second=details_second)
#Logging Out    
@app.route('/logout')
def logout():
    start=time.time()
    time_global.append(start)
    clicked.append('logout')
    print(time_global)
    print(clicked)
    session_time=time_global[-1]-time_global[0]
    print('customer id is',cust_id_logged_in)
    print('session_time',session_time)
    timespent=[]
    for i in range(0,(len(time_global)-1)):
        timespent.append(time_global[i+1]-time_global[i])
    timespent.append(0)
    print(cust_id_logged_in)
    print(timespent)
    a={'activity':clicked,'Timespent':timespent}
    Session_info=pd.DataFrame(a)
    print(Session_info)
    print(clicked)
    print(timespent)
    print(Session_info)
    print(added_to_cart_and_removed)
    if (len(added_to_cart_and_removed)>0):
        send_mail()
    time_global.clear()
    clicked.clear()
    added_to_cart_and_removed.clear()
    cart_id_1.clear()
    cust_id_logged_in.clear()
    return render_template('index.html')


#Viewing customers previous orders 
@app.route('/Your_Orders')
def Your_Orders():
    cust_id=cust_id_logged_in[0]
    start=time.time()
    time_global.append(start)
    clicked.append('previous orders')
    index_pos=test_data1[test_data1['customer_id']==cust_id].index.values
    arts=test_data1.iloc[index_pos[0],1]
    print(arts)
    img_name=[]
    price_previous=[]
    product_name_previous=[]
    for i in arts:
        pd=price_details[price_details['article_id']==int(i)]['price'].values
        price_previous.append(np.round(((np.round(pd[0]*100000)/10)*10)/10)*10)
        pname=price_details[price_details['article_id']==int(i)]['prod_name'].values
        product_name_previous.append(pname[0])
        i=str(i)
        path=f"/static/images/0{i[0:2]}/0{i}.jpg"
        img_name.append(path)
    print(sum(price_previous))
    print(img_name)
    cart_details_final=list(zip(product_name_previous,price_previous,img_name))
    return render_template('cart.html',ab=cart_details_final,total_price=sum(price_previous))
    #for a in arts:
    #    art_index=article1[article1.article_id==a].index.values
    #    products.append(article1.at[art_index[0],'product_type_name'])
    #    items.append(a)
    #return render_template('main.html',time_global=img_path)
    

#Delete From Cart. And this gets recorded in the added_to_cart_and_removed list    
@app.route('/remove_from_cart')
def remove_from_cart():
    start=time.time()
    time_global.append(start)
    clicked.append('removing from cart')
    selectedImage = request.args.get('filename')
    b=selectedImage[7:]
    print(cart_id_1)
    selectedImage1=int(selectedImage[-13:-4])
    print(selectedImage1)
    added_to_cart_and_removed.append(selectedImage1)
    cart_id_1.remove(str(selectedImage1))
    img_name=[]
    price_cart=[]
    product_name_cart=[]
    for i in cart_id_1:
        pd=price_details[price_details['article_id']==int(i)]['price'].values
        price_cart.append(np.round(((np.round(pd[0]*100000)/10)*10)/10)*10)
        pname=price_details[price_details['article_id']==int(i)]['prod_name'].values
        product_name_cart.append(pname[0])
        path=f"/static/images/0{i[0:2]}/0{i}.jpg"
        img_name.append(path)
    print(sum(price_cart))
    print(img_name)
    print(added_to_cart_and_removed)
    cart_details_final=list(zip(product_name_cart,price_cart,img_name))
    return render_template('cart.html',ab=cart_details_final,total_price=sum(price_cart))


#Trigger a mail to customer who added a product to the list and then removed it. 
def send_mail():
    print(added_to_cart_and_removed)
    path_store_mail=[]
    prod_name_mail=[]
    price_mail=[]
    desc_mail=[]
    for i in added_to_cart_and_removed:
        a=str(i)
        p=price_details[price_details['article_id']==int(a)]['price'].values
        pn=price_details[price_details['article_id']==int(a)]['prod_name'].values
        d=price_details[price_details['article_id']==int(a)]['detail_desc'].values
        path=f"/static/images/0{a[0:2]}/0{a}.jpg"
        path_store_mail.append(path)
        price_mail.append(np.round(((np.round(p[0]*100000)/10)*10)/10)*10)
        prod_name_mail.append(pn[0])
        desc_mail.append(d[0])
    path=os.path.join(os.getcwd(), 'static', 'images','0'+(str(added_to_cart_and_removed[0])[0:2]),'0'+str(added_to_cart_and_removed[0])+'.jpg')
    print(path)
#path=str(pathlib.Path(path1).absolute())
#print(path)
    pythoncom.CoInitialize()
    outlook=client.Dispatch('Outlook.Application')
    msg=outlook.CreateItem(0)
    msg.Display()
    msg.To='sauravbaliga17@gmail.com'
    msg.Subject='DISCOUNT DISCOUNT DISCOUNT DISCOUNT'
    image=msg.Attachments.Add(path)
    html_body = """
    <html>
    <body>
    <div>
        <h1 style="font-family: 'Haderen Park'; font-size: 30; font-weight: bold; color: #052f63;"> Hi {},</h1>
        <span style="font-family: 'Haderen Park'; font-size: 20; color: #073b7c;"> Discount Prices Slashed Use code FASHION and get 50% off</span>
    </div><br>
    <div>
        <img src="cid:highlight-img" width='100'/>
    </div>
    <span style="font-family: 'Haderen Park'; font-size: 20; font-weight:bold; color: #052f63;">Regards<br/> H&M </span>
    </body>
    </html>
    """

# code for changing the content id of the image
    image.PropertyAccessor.SetProperty("http://schemas.microsoft.com/mapi/proptag/0x3712001F", "highlight-img")
    msg.HTMLBody=html_body.format(cust_id_logged_in)
    msg.Display()
    msg.Send()



#Right Left Swipe Game
@app.route('/Lets_Get_To_Know_You',methods=['GET','POST'])
def LGTKY():
    cust_id=cust_id_logged_in[0]
    index_pos=test_data1[test_data1['customer_id']==cust_id].index.values
    arts=test_data1.iloc[index_pos[0],1]
    products_1=[]
    items_1=[]
    final_list=[]
    for a in arts:
        art_index=article1[article1.article_id==a].index.values
        products_1.append(article1.at[art_index[0],'product_type_name'])
        items_1.append(a)
    unique_items=pd.DataFrame()
    unique_items['products']=pd.Series(products_1)
    unique_items['article_ids']=pd.Series(items_1)
    unique_products=unique_items.groupby('products')['article_ids'].agg(list).reset_index()
    for i,j in zip(unique_products['products'],unique_products['article_ids']):
        arts_list=[]
        for x in j:
            #print(x)
            arts_list.append(str(x))
            for i in arts_list:
                final_list.append(i)
    final_list=list(set(final_list))
    print(final_list)
    similar_list=[]
    for ids in final_list[:]:
        idd = str(ids)
        print(idd)
        similar_items = list(item_similarities1[item_similarities1['item']==int(idd)]['similar_items'])[0][1:]
        print(similar_items)
        similar_list.append(similar_items)
    print(similar_list)
    new_sim_list = itertools.chain(*similar_list)
    new_sim_list=list(new_sim_list)
    print(new_sim_list)
    images_random = random.sample(new_sim_list,5)
    images_for_swipe.append(list(list(images_random)))
    print(images_for_swipe)
    img_path_swipe=[]
    for i,x in enumerate(images_for_swipe[0]):
        id = str(x)
        path = f"/static/images/0{id[0:2]}/0{id}.jpg"
        img_path_swipe.append(path)
    price_r_item=[]
    prod_name_r_item=[]
    desc_r_item=[]
    for i in images_for_swipe[0]:
        price_r=price_details[price_details['article_id']==int(i)]['price'].values
        price_r_item.append(np.round(((np.round(price_r[0]*100000)/10)*10)/10)*10)
        prod_name_r=price_details[price_details['article_id']==int(i)]['prod_name'].values
        prod_name_r_item.append(prod_name_r[0])
        desc_r=price_details[price_details['article_id']==int(i)]['detail_desc'].values
        desc_r_item.append(desc_r[0])
    print(price_r_item)
    print(prod_name_r_item)
    print(desc_r_item)
    det_p_rec=list(zip(img_path_swipe,price_r_item,prod_name_r_item,desc_r_item))
    print(det_p_rec)
    return render_template('index_swipe_1.html',details=det_p_rec)

#Store the swipe details from the front end using ajax method.
@app.route('/swiperesult',methods=['GET','POST'])
def create_entry():
        req=request.get_json()
        swipe_details.append(req)
        print(req)
        print(swipe_details)
        res=make_response(jsonify({'message':'JSON Recieved'}),200)
        return jsonify({
            'req':req
        }
        )
#Search for a product.(ajax method)
@app.route('/search',methods=['GET','POST'])
def create_search():
        req=request.get_json()
        search_details.append(req)
        print(req)
        print(search_details)
        res=make_response(jsonify({'message':'JSON Recieved'}),200)
        return jsonify({
            'req':req
        }
        )

#Search Result     
@app.route('/search_result',methods=['GET',"POST"])
def search():
    start=time.time()
    time_global.append(start)
    print(search_details)
    item1=search_details[0]
    path_store=[]
    price=[]
    prod_name=[]
    desc=[]
    print('item name',item1)
    print(item1[0])
    sim_ratio=[]
    for i in products1:
        sim_ratio.append(SequenceMatcher(None, item1[0], i).ratio())
    print(sim_ratio)
    max_value=max(sim_ratio)
    index = sim_ratio.index(max_value)
    print(index)
    print(products1[index])
    i=products1[index]
    clicked.append(item1[0])
    #item1=list(chain.from_iterable(item1))
    #print('after flatten',item1)
    print('products',products)
    print('inside if loop',item1)
    articles_list=article1[article1['product_type_name']==i]['article_id'].to_list()
    trans_art1=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
    trans_arts1=trans_art1.groupby('article_id')['customer_id'].agg(list).reset_index()
    trans_arts1['counts']=trans_arts1['customer_id'].apply(lambda x: len(x))
    trans_arts1=trans_arts1.sort_values('counts',ascending=False).head(10)
    print(trans_arts1.head())
    rows=2
    for num, x in enumerate(trans_arts1['article_id']):
        a=str(x)
        p=price_details[price_details['article_id']==int(a)]['price'].values
        pn=price_details[price_details['article_id']==int(a)]['prod_name'].values
        d=price_details[price_details['article_id']==int(a)]['detail_desc'].values
        path=f"/static/images/0{a[0:2]}/0{a}.jpg"
        path_store.append(path)
        price.append(np.round(((np.round(p[0]*100000)/10)*10)/10)*10)
        prod_name.append(pn[0])
        desc.append(d[0])
    det=list(zip(path_store,price,prod_name,desc))
    search_details.clear()
    return render_template('home.html', images = det)


@app.route('/rewards',methods=['GET','POST'])
def new_rewards():
    res = ''.join(random.choices(string.ascii_uppercase +
                             string.digits, k=6))
    return render_template('scratch_card.html',code=str(res))

@app.route('/rewards1',methods=['GET','POST'])
def your_rewards():
    a=scratch_card_coupon
    return render_template('scratch_card1.html',req=a)


#Scratch Card
@app.route('/scratch_card',methods=['GET','POST'])
def create_entry1():
        req=request.get_json()
        scratch_card_coupon.append(req)
        print(req)
        res=make_response(jsonify({'message':'JSON Recieved'}),200)
        return jsonify({
            'req':req
        }
        )

if __name__ == '__main__':
  app.run(debug=True,use_reloader=False)