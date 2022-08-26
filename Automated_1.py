import win32com.client as client
import pathlib
import cv2
import os 
a=[411413001,411413001]
path_store=[]
for i in a:
    path=os.path.join(os.getcwd(), 'static', 'images','0'+(str(i)[0:2]),'0'+str(i)+'.jpg')
    path_store.append(path)

#path=str(pathlib.Path(path1).absolute())
#print(path)

outlook=client.Dispatch('Outlook.Application')
msg=outlook.CreateItem(0)
msg.Display()
msg.To='saurav.baliga@convergytics.com'
msg.Subject='Highlights of Titanic dataset'
#image=msg.Attachments.Add(path_store)
html_body = """
    <html>
    <body>
    <div>
        <h1 style="font-family: 'Haderen Park'; font-size: 30; font-weight: bold; color: #052f63;"> Hi {},</h1>
        <span style="font-family: 'Haderen Park'; font-size: 20; color: #073b7c;"> Discount Prices Slashed Use code FASHION and get 50% off</span>
    </div><br>
    {% for i in """+path_store+""" %}
    <div>
        <img src="cid:highlight-img" width='100'/>
        <img src={{i}} width=100/>
    </div>
    {% endfor %}
    <span style="font-family: 'Haderen Park'; font-size: 20; font-weight:bold; color: #052f63;">Regards<br/> H&M </span>
    </body>
    </html>
    """

# code for changing the content id of the image
#image.PropertyAccessor.SetProperty("http://schemas.microsoft.com/mapi/proptag/0x3712001F", "highlight-img")
msg.HTMLBody=html_body.format('User Name',path_store)
msg.Display()
#msg.Send()


