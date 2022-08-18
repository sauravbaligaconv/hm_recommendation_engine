from flask import Flask,request
from flask import render_template
import os
import pandas as pd
from numpy.testing import assert_almost_equal
import numpy as np

app = Flask(__name__)
cart_id_1=[]
#embeds=pd.read_csv('static/data/similarities.csv')
df=pd.read_csv('static/data/1_sim.csv')
for i in range(2,6):
    df1=pd.read_csv('static/data/{}_sim.csv'.format(i))
    final=pd.concat([df,df1],axis=0)
    df=final
    print(df.shape)
embeds=df
embeds=embeds.set_index('path')
images=pd.read_csv('static/data/img_pres.csv')
images=images.drop('Unnamed: 0',axis=1)
images.rename(columns={'0':'img_id'},inplace=True)
images['ids']=images['img_id'].apply(lambda x:x[1:10])
images['path']=images['img_id'].apply(lambda x: f"images/{x[0:3]}/{x}")
ids=images['ids'][0:5000]
ids=[int(x) for x in ids]
articles=pd.read_csv('static/data/articles.csv')
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
df=pd.read_csv('static/data/1.csv')
for i in range(2,39):
    df1=pd.read_csv('static/data/{}.csv'.format(i))
    final=pd.concat([df,df1],axis=0)
    df=final
    print(df.shape)
transactions=df
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
products=list(articles['product_type_name'].unique())
print('home   :',products)
item='shirt'
path_store=[]
price=[]
prod_name=[]
desc=[]
for i in products:
    if str(item) in i.lower().strip():
        articles_list=articles[articles['product_type_name']==i]['article_id'].to_list()
        trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
        trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
        trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
        trans_arts=trans_arts.sort_values('counts',ascending=False).head(10)
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
print('shirts product name:',prod_name)
#print('loading the images')
#print(path_store[10])
#images1=[]
#for file in path_store:
#       with open(file, "rb") as image:
#            encoded = base64.b64encode(image.read()).decode()
#            images1.append(f"data:image/jpeg;base64,{encoded}")
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


@app.route("/")
@app.route("/home")
# Need to write a function that is called when opening the site

def home():
    #print(images)
    det=list(zip(path_store,price,prod_name,desc))
    return render_template('home.html', images = det)
@app.route("/recommend")
# Need to write a function that is called when opening recommendations
def recommend():
    selectedImage = request.args.get('selectedImage')
    b=selectedImage[7:]
    selectedImage1=int(selectedImage[-13:-4])
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
    
@app.route("/recommend1")
# Need to write a function that is called when opening recommendations
def recommend1():
    selectedImage = request.args.get('selectedImage')
    selectedImage1=int(selectedImage[-13:-4])
    print('rec1',selectedImage1)
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

@app.route('/quick_add')
def quick_add():
    selectedImage = request.args.get('filename')
    id=selectedImage[-13:-4]
    cart_id_1.append(id)
    print(cart_id_1)
    det=list(zip(path_store,price,prod_name,desc))
    return render_template('home.html',images=det)

@app.route('/cart')
def check_cart():
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


@app.route('/shirts')
def shirts():
    item1='shirt'
    print(item1)
    path_store_shirt=[]
    price_shirt=[]
    prod_name_shirt=[]
    desc_shirt=[]
    print('inside shirt:')
    print(products)
    for i in products:
        print(i)
        if str(item1) in i.lower().strip():
            articles_list=articles[articles['product_type_name']==i]['article_id'].to_list()
            trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
            trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
            trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
            trans_arts=trans_arts.sort_values('counts',ascending=False).head(10)
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
    return render_template('home.html', images = det_shirt)

@app.route('/shorts')
def shorts():
    item1='shorts'
    print(item1)
    path_store_shirt=[]
    price_shirt=[]
    prod_name_shirt=[]
    desc_shirt=[]
    print('inside shirt:')
    print(products)
    for i in products:
        print(i)
        if str(item1) in i.lower().strip():
            articles_list=articles[articles['product_type_name']==i]['article_id'].to_list()
            trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
            trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
            trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
            trans_arts=trans_arts.sort_values('counts',ascending=False).head(10)
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
    return render_template('home.html', images = det_shirt)



@app.route('/socks')
def socks():
    item1='socks'
    print(item1)
    path_store_shirt=[]
    price_shirt=[]
    prod_name_shirt=[]
    desc_shirt=[]
    print('inside shirt:')
    print(products)
    for i in products:
        print(i)
        if str(item1) in i.lower().strip():
            articles_list=articles[articles['product_type_name']==i]['article_id'].to_list()
            trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
            trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
            trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
            trans_arts=trans_arts.sort_values('counts',ascending=False).head(10)
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
    return render_template('home.html', images = det_shirt)

@app.route('/watch')
def watch():
    item1='watch'
    print(item1)
    path_store_shirt=[]
    price_shirt=[]
    prod_name_shirt=[]
    desc_shirt=[]
    print('inside shirt:')
    print(products)
    for i in products:
        print(i)
        if str(item1) in i.lower().strip():
            articles_list=articles[articles['product_type_name']==i]['article_id'].to_list()
            trans_art=transactions[transactions['article_id'].isin(articles_list)][['customer_id','article_id','price']]
            trans_arts=trans_art.groupby('article_id')['customer_id'].agg(list).reset_index()
            trans_arts['counts']=trans_arts['customer_id'].apply(lambda x: len(x))
            trans_arts=trans_arts.sort_values('counts',ascending=False).head(10)
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
    return render_template('home.html', images = det_shirt)




if __name__ == '__main__':
  app.run(debug=True)