# web-app for API image manipulation

from flask import Flask, request, render_template, send_from_directory,url_for
import os
from PIL import Image
import numpy as np
import json
# urllib.request to make a request to api
import urllib2
from urllib2 import urlopen




app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))


# default access page
@app.route('/', methods =['POST', 'GET']) 
def main():
    return render_template('index.html')

@app.route("/bills")
def bills():
    return render_template("bills.html")

@app.route("/imageviewer", methods =['POST', 'GET'])
def imageviewer():
    if request.method == 'POST': 
        city = request.form['city'] 
    else: 
        # for default name washingotn 
        city = 'washington'
    
    # source contain json data from api
    source = urllib2.urlopen('http://api.openweathermap.org/data/2.5/weather?q=' + city + '&units=imperial&appid=3011b303e0f1a936b399b9b7e007f3f4').read()

    # converting json data to dictionary

    list_of_data = json.loads(source)
    a = str(list_of_data['main']['temp'])
    b = float(a)

    c = str(list_of_data['main']['pressure'])
    d = float(c)

    

    # data for variable list_of_data
    data = {
        "name": str(list_of_data['name']),
        "country_code": str(list_of_data['sys']['country']),
        "coordinate": str(list_of_data['coord']['lon']) + ' ' + str(list_of_data['coord']['lat']),
        "temp": str(list_of_data['main']['temp']) + 'k',
        "pressure": str(list_of_data['main']['pressure']),
        "humidity": str(list_of_data['main']['humidity']),
        "futuretemp": b + 39.2,
        "futurepressure": d - 182.2,
        "predictedsealevel": ((d-182.2)/140),
        
    }
    return render_template("imageviewer.html", data = data)


# upload selected image and forward to processing page
@app.route("/upload", methods=["POST"])
def upload():
    target = os.path.join(APP_ROOT, 'static/images/')

    # create image directory if not found
    if not os.path.isdir(target):
        os.mkdir(target)

    # retrieve file from html file-picker
    upload = request.files.getlist("file")[0]
    print("File name: {}".format(upload.filename))
    filename = upload.filename

    # file support verification
    ext = os.path.splitext(filename)[1]
    if (ext == ".jpg") or (ext == ".png") or (ext == ".bmp"):
        print("File accepted")
    else:
        return render_template("error.html", message="The selected file is not supported"), 400

    # save file
    destination = "/".join([target, filename])
    print("File saved to to:", destination)
    upload.save(destination)

   

    
    return render_template("processing.html", image_name=filename)


# rotate filename the specified degrees
@app.route("/rotate", methods=["POST"])
def rotate():
    # retrieve parameters from html form
    angle = request.form['angle']
    filename = request.form['image']

    # open and process image
    target = os.path.join(APP_ROOT, 'static/images')
    destination = "/".join([target, filename])

    img = Image.open(destination)
    img = img.rotate(-1*int(angle))

    # save and return image
    destination = "/".join([target, 'temp.png'])
    if os.path.isfile(destination):
        os.remove(destination)
    img.save(destination)

    return send_image('temp.png')


# flip filename 'vertical' or 'horizontal'
@app.route("/flip", methods=['POST','GET'])
def flip():

    # retrieve parameters from html form
    if 'horizontal' in request.form['mode']:
        mode = 'horizontal'
    elif 'vertical' in request.form['mode']:
        mode = 'vertical'
    else:
        return render_template("error.html", message="Mode not supported (vertical - horizontal)"), 400
    filename = request.form['image']

    # open and process image
    target = os.path.join(APP_ROOT, 'static/images')
    destination = "/".join([target, filename])

    img = Image.open(destination).convert('RGB')
    HSVim = img.convert('HSV')
    # Make numpy versions
    RGBna = np.array(img)
    HSVna = np.array(HSVim)

    # Extract Hue
    H = HSVna[:,:,0]

    # Find all green pixels, i.e. where 100 < Hue < 140
    lo,hi = 70,140
    # Rescale to 0-255, rather than 0-360 because we are using uint8
    lo = int((lo * 255) / 360)
    hi = int((hi * 255) / 360)
    green = np.where((H>lo) & (H<hi))

    # Make all green pixels black in original image
    RGBna[green] = [0,0,0]

    if mode == 'horizontal':
        img = Image.fromarray(RGBna)
    


    
    

    # save and return image
    destination = "/".join([target, 'new.png'])
    if os.path.isfile(destination):
        os.remove(destination)
    img.save(destination)
    



    return send_image('new.png')
    # return render_template("imageviewer.html")

    


# crop filename from (x1,y1) to (x2,y2)
@app.route("/crop", methods=["POST"])
def crop():
    # retrieve parameters from html form
    x1 = int(request.form['x1'])
    y1 = int(request.form['y1'])
    x2 = int(request.form['x2'])
    y2 = int(request.form['y2'])
    filename = request.form['image']

    # open image
    target = os.path.join(APP_ROOT, 'static/images')
    destination = "/".join([target, filename])

    img = Image.open(destination)

    # check for valid crop parameters
    width = img.size[0]
    height = img.size[1]

    crop_possible = True
    if not 0 <= x1 < width:
        crop_possible = False
    if not 0 < x2 <= width:
        crop_possible = False
    if not 0 <= y1 < height:
        crop_possible = False
    if not 0 < y2 <= height:
        crop_possible = False
    if not x1 < x2:
        crop_possible = False
    if not y1 < y2:
        crop_possible = False

    # crop image and show
    if crop_possible:
        img = img.crop((x1, y1, x2, y2))
        
        # save and return image
        destination = "/".join([target, 'temp.png'])
        if os.path.isfile(destination):
            os.remove(destination)
        img.save(destination)
        return send_image('temp.png')
    else:
        return render_template("error.html", message="Crop dimensions not valid"), 400
    return '', 204


# blend filename with stock photo and alpha parameter
@app.route("/blend", methods=["POST"])
def blend():
    # retrieve parameters from html form
    alpha = request.form['alpha']
    filename1 = request.form['image']

    # open images
    target = os.path.join(APP_ROOT, 'static/images')
    filename2 = 'blend.jpg'
    destination1 = "/".join([target, filename1])
    destination2 = "/".join([target, filename2])

    img1 = Image.open(destination1)
    img2 = Image.open(destination2)

    # resize images to max dimensions
    width = max(img1.size[0], img2.size[0])
    height = max(img1.size[1], img2.size[1])

    img1 = img1.resize((width, height), Image.ANTIALIAS)
    img2 = img2.resize((width, height), Image.ANTIALIAS)

    # if image in gray scale, convert stock image to monochrome
    if len(img1.mode) < 3:
        img2 = img2.convert('L')

    # blend and show image
    img = Image.blend(img1, img2, float(alpha)/100)

     # save and return image
    destination = "/".join([target, 'temp.png'])
    if os.path.isfile(destination):
        os.remove(destination)
    img.save(destination)

    return send_image('temp.png')


# retrieve file from 'static/images' directory
@app.route('/static/images/<filename>')
def send_image(filename):
    return send_from_directory("static/images", filename)


if __name__ == "__main__":
    app.run()

