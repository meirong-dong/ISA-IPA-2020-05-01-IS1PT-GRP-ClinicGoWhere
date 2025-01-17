# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 15:24:29 2020

@author: meiro
"""
#Flask Libraries
from flask import Flask, render_template,session, request,make_response
from flask import redirect,abort,url_for,flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from forms import ClinicForm
#Machine Learning Libraries
import pandas as pd
import numpy as np
import time,folium,requests,json,googlemaps,pytz
import joblib as joblib
import datetime as datetime

app = Flask(__name__)
bootstrap = Bootstrap(app)
moment = Moment(app)

app.config['SECRET_KEY'] = 'there is a need for a secret key'

#covert postal code to coordinates
def get_coordinates(postal_code):
    # define variables based on API requirements
    postal_code = postal_code
    page = 1
    results = []

    while True:
        try:
            # usage:/commonapi/search?searchVal={SearchText}&returnGeom={Y/N}&getAddrDetails={Y/N}&pageNum={PageNumber}
            response = requests.get(
                'http://developers.onemap.sg/commonapi/search?searchVal={0}&returnGeom=Y&getAddrDetails=Y&pageNum={1}'
                .format(postal_code, page)).json()
        except requests.exceptions.ConnectionError as e:
            print('Fetching {} failed. Retrying in 2 sec'.format(postal_code))
            time.sleep(2)
            continue
        results = response['results']
        if response['totalNumPages'] > page:
            page = page + 1
        else:
            break
    return results

def loaded_model(filename):
    filename = filename
    loaded_model = joblib.load(filename)
    return loaded_model

def loaded_clinics():
    path_full = "data/clinic_final.csv"
    path_cluster = "data/clusters.csv"
    clinic_full = pd.read_csv(path_full) # get all the clinic list
    coordinates = pd.read_csv(path_cluster) #get all the clusters
    return clinic_full,coordinates

def googlemap(clinics,latitude,longitude):
    # search google map for distance and timing
    google_maps = googlemaps.Client(key='Your Google API')
    clinics['Distance'] = pd.Series(np.zeros(len(clinics)), index=clinics.index)
    clinics['Travel Time'] = pd.Series(np.zeros(len(clinics)), index=clinics.index)

    for index, row in clinics.iterrows():
        # Assign latitude and longitude as origin/departure points
        origins = (float(latitude), float(longitude))
        # Assign latitude and longitude from the next row as the destination point
        destination = (row['Latitude'], row['Longitude'])
        # pass origin and destination variables to distance_matrix function# output in meters
        result = google_maps.distance_matrix(origins, destination, mode='walking')["rows"][0]["elements"][0]["distance"]["value"]
        clinics.loc[index, 'Distance'] = result
        now = datetime.datetime.now()
        directions = google_maps.directions(origins, destination, mode='walking', departure_time=now)
        travel_time = directions[0].get('legs')[0].get('duration').get('text')
        clinics.loc[index, 'Travel Time'] = travel_time

    clinics_list = clinics.sort_values(by=['Distance'], ascending=True)
    clinics_list = clinics_list.head(10)
    clinics_list = clinics_list.reset_index()
    return clinics_list

@app.route('/',methods=['GET','POST'])
def index():
    tz = pytz.timezone('Asia/Singapore')
    current_time = datetime.datetime.now(tz=tz)
    flash('Stay at home if you feel unwell. If you have a fever, cough and difficulty breathing, '
          'seek medical attention and call in advance. '
          'Follow the directions of your local health authority. '
          'Source: World Health Organisation')
    #postal_code = None
    form = ClinicForm()
    session['postal_code'] = None
    if form.validate_on_submit():
        session['postal_code'] = form.postal_code.data
        return redirect(url_for('results'))
    else:
        session['postal_code'] = None
    return render_template('index.html',
                           current_time=current_time, form=form,
                           postal_code=session['postal_code'],flash=flash)

@app.route('/results',methods=['GET','POST'])
def results():
    tz = pytz.timezone('Asia/Singapore')
    current_time = datetime.datetime.now(tz=tz)
    flash('Stay at home if you feel unwell. If you have a fever, cough and difficulty breathing, '
          'seek medical attention and call in advance. '
          'Follow the directions of your local health authority. '
          'Source: World Health Organisation')
    if session['postal_code']:
        #covert the input value
        buildings = get_coordinates(session['postal_code'])
        if buildings:
            latitude = buildings[0]['LATITUDE']
            longitude = buildings[0]['LONGITUDE']
            address = buildings[0]['ADDRESS']
            user_input = np.array([float(latitude), float(longitude)])
            user_input = user_input.reshape(1, -1)
            #load the trained model & data
            model = loaded_model('data/final_model.sav')
            clinic_full, coordinates = loaded_clinics()
            #predict the input's cluster and find out all the coordinates in the cluster
            cluster_labels_predicted = model.predict(user_input)
            clinic_cluster = coordinates.loc[coordinates['kmeans'] == int(cluster_labels_predicted)]
            clinic_full['Latitude'] = clinic_full['Latitude'].astype(float)
            clinic_full['Longitude'] = clinic_full['Longitude'].astype(float)
            clinic_cluster ['Latitude'] = clinic_cluster ['Latitude'].astype(float)
            clinic_cluster ['Longitude'] = clinic_cluster ['Longitude'].astype(float)
            clinics = pd.merge(clinic_full, clinic_cluster, how='left', on=['Latitude','Longitude'])
            clinics = clinics.loc[clinics['kmeans'] == int(cluster_labels_predicted)]
            clinics_list = googlemap(clinics,latitude,longitude)
            clinics_list['Contact Number'] = clinics_list['Contact Number'].astype(np.int64)
        else:
            session['postal_code'] = None
            latitude = None
            longitude = None
            cluster_labels_predicted = None
            address = None
            clinics = None
            clinics_list = None
    return render_template('results.html',
                           current_time=current_time,postal_code=session['postal_code'],
                           latitude=latitude,longitude=longitude,
                           cluster_labels_predicted=cluster_labels_predicted,
                           address=address,clinics=clinics,clinics_list=clinics_list)
@app.route('/get_map')
def get_map():
    tz = pytz.timezone('Asia/Singapore')
    current_time = datetime.datetime.now(tz=tz)
    return render_template('map.html',current_time=current_time)

@app.errorhandler(400)
def bad_request(e):
    return render_template('400.html'), 400

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
