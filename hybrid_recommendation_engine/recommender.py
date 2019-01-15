# -*- coding: utf-8 -*-
"""
Restaurant Hybrid Recommendation Engine:
Created on Tue Jan 15 10:34:03 2019 @author: jingzhao

Watermarks:
python 3.6.5
ipython 6.4.0
numpy 1.15.0
pandas 0.23.3
geopy 1.17.0
sklearn 0.19.1

Github repo: 
https://github.com/jingzhaomirror/capstone2_hybrid_yelp_recommender.git
"""

# import necessary modules to support the recommendation engine
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import pickle
import os.path
from sklearn.metrics.pairwise import linear_kernel

# function for calculating geodesic distance between two points
def great_circle_mile(lat1, lon1, lat2, lon2):
    """
    Compute geodesic distances (great-circle distance) of two points on the globe given their coordinates. 
    The function returns the distance in miles. 
    Note: 1. Calculation uses the earth's mean radius of 6371.009 km, 
    2. The central subtended angle is calculated by formula: 
    alpha = cos-1*[sin(lat1)*sin(lat2)+ cos(lat1)*cos(lat2)*cos(lon1-lon2)]
    """
    
    from math import sin, cos, acos, radians
    
    lat1, lon1, lat2, lon2 = radians(lat1), radians(lon1), radians(lat2), radians(lon2) # convert degrees to radians
    earth_radius = 6371.009  # use earth's mean radius in kilometers
    alpha = acos(sin(lat1)*sin(lat2) + cos(lat1)*cos(lat2)*cos(lon1-lon2)) # alpha is in radians
    dis_km = alpha * earth_radius
    dis_mile = dis_km * 0.621371   # convert kilometer to mile
    
    return dis_mile

# recommender class
class Recommender:
    
    def __init__(self, n=5, original_score=False, personalized=False):
        """initiate a Recommender object.
        ---
        Optional keyword arguments to be passed are:
        1. the desired number of recommendations to make ('n'), the default number is 10.
        2. the score for ranking the recommendations ('original_score'): by default, the adjusted score will be used for ranking; 
            To rank by the original average rating of the restaurant, pass original_score=True
        3. 'personalized': a boolean to indicate if additional data needs to be loaded to compute personalized recommendations. 
        ---
        In addition, a few class variables will be initiated upon creation for internal use:        
        1. the class variable '.module' is used to keep track of whether a personalized recommendation is available or not.
            it only takes one of the following values with the default being 0
            0: no personalization yet
            1: a personalized recommendation has been computed using the collaborative module
            2: a personalzied recommendation has been computed using the content-based module
        2. the class variable '.column_to_dispay' is used to keep track of a list of column names to display in the recommendation results.
            the list will be updated based on the modules being called.
        3. the class variable '.recomm' is used to store the current list of recommendations
        """
        
        # import datasets needed to power the recommendation engine
        self.business = pd.read_csv('business_clean.csv')  # contains business data including location data, attributes and categories
        self.business['postal_code'] = self.business.postal_code.astype(str) # update the data type of the 'postal_code' column to string
        self.review = pd.read_csv('review_clean.csv') # contains full review text data including the user_id that wrote the review and the business_id the review is written for
        # a subset of reviews related to restaurants
        self.review_s = self.review[self.review.business_id.isin(self.business.business_id.unique())]
        # add 'adjusted_score' to the 'business' dataset, which adjusts the restaurnat average star ratings by the number of ratings it has
        globe_mean = ((self.business.stars * self.business.review_count).sum())/(self.business.review_count.sum())
        k = 22 # set dumping strength k to 22, which is the 50% quantile of the review counts for all businesses
        self.business['adjusted_score'] = (self.business.review_count * self.business.stars + k * globe_mean)/(self.business.review_count + k)
        
        # initiate other class variables
        self.n = n # number of recommendations to make, default is 5
        self.original_score = original_score # boolean indicating whether the original average rating or the adjusted score is used
        self.module = 0 # variable indicating which recommender module is used, default is 0
        self.column_to_display = ['state','city','name','address','attributes.RestaurantsPriceRange2','cuisine',\
                                  'style','review_count','stars','adjusted_score'] # initiate a list of columns to display in the recommendation results
        
        # upon class creation, initiate the recommendation to be all the open restaurants from the entire catalog of 'business' dataset sorted by the score of interest
        if self.original_score:  # set sorting criteria to the originial star rating
            score = 'stars'
        else:  # set sorting criteria to the adjusted score
            score = 'adjusted_score'
        self.recomm = self.business[self.business.is_open == 1].sort_values(score, ascending=False)
        
        # pre-load additional information if personalized modules are desired
        if personalized:
            
            # load information for collaborative module
            with open('svd_trained_info.pkl', 'rb') as f:
                self.svd_trained_info = pickle.load(f)
                
            # load information for content-based module
            with open('rest_pcafeature_all.pkl', 'rb') as f: 
                self.rest_pcafeature = pickle.load(f)   # load the saved restaurant pcafeature vectors
            max_bytes = 2**31 - 1
            bytes_in = bytearray(0)
            input_size = os.path.getsize('user_pcafeature_all.pkl')
            with open('user_pcafeature_all.pkl','rb') as f: 
                for _ in range(0, input_size, max_bytes):
                    bytes_in += f.read(max_bytes)
                self.user_pcafeature = pickle.loads(bytes_in)  # load the saved user pcafeature vectors
           
    def _filter_by_location(self):
        """Filter and update the dataframe of recommendations by the matching location of interest.
        A combination of state, city and zipcode is used as the location information, partially missing information can be handled. 
        Matching restaurant is defined as the restaurant within the acceptable distance (max_distance) of the location of interest.
        note: this hidden method should only be called within the method 'keyword'
        """       
        geolocator = Nominatim(user_agent="yelp_recommender") # use geopy.geocoders to make geolocation queries
        address = [self.city, self.state, self.zipcode]
        address = ",".join([str(i) for i in address if i != None])
        # use geolocate query to find the coordinate for the location of interest
        try:
            location = geolocator.geocode(address, timeout=10) 
        except GeocoderTimedOut as e:
            print("Error: geocode failed to locate the address of interest {} with message {}".format(address, e.message))            

        # calculate the geodesic distance between each restaurant and the location of interest and add as a new column ''distance_to_interest'
        self.recomm['distance_to_interest'] = self.recomm.apply(lambda row: great_circle_mile(row.latitude, row.longitude, location.latitude, location.longitude), axis=1)
        # add the new column 'distance_to_interest' to the list of columns to display in the recommendation result
        self.column_to_display.insert(0, 'distance_to_interest')
        # filter by the desired distance
        self.recomm = self.recomm[self.recomm.distance_to_interest <= self.max_distance]

    def _filter_by_state(self):
        """ Filter and update the dataframe of recommendations by the matching state.
        note: this hidden method should only be called within the method 'keyword'
        """
        self.recomm = self.recomm[self.recomm.state == self.state.upper()]
    
    def _filter_by_cuisine(self):
        """ Filter and update the dataframe of recommendations by the matching cuisine of interest. 
        note: this hidden method should only be called within the method 'keyword'
        """                         
        idx = []
        for i in self.recomm.index: 
            if self.recomm.loc[i,'cuisine'] is not np.nan:
                entries = self.recomm.loc[i,'cuisine'].split(',')
                if self.cuisine in entries:
                    idx.append(i)
        self.recomm = self.recomm.loc[idx]
    
    def _filter_by_style(self):  
        """ Filter and update the dataframe of recommendations by the matching style of interest. 
        note: this hidden method should only be called within the method 'keyword'
        """
        idx = []
        for i in self.recomm.index: 
            if self.recomm.loc[i,'style'] is not np.nan:
                entries = self.recomm.loc[i,'style'].split(',')
                if self.style in entries:
                    idx.append(i)
        self.recomm = self.recomm.loc[idx]
        
    def _filter_by_price(self):
        """Filter and update the dataframe of recommendations by the matching price range of interest. 
        note: this hidden method should only be called within the method 'keyword'
        """
        self.recomm = self.recomm[self.recomm['attributes.RestaurantsPriceRange2'].isin(self.price)]
    
    def display_recommendation(self, n=5):
        """ Display the list of top n recommended restaurants
        """
        self.n = n # update the number of recommendations to display
        if len(self.recomm) == 0:
            print("Sorry, there is no matching recommendations.")
        elif self.n < len(self.recomm):  # display only the top n from the recommendation list
            print("Below is a list of the top {} recommended restaurants for you: ".format(self.n))
            print(self.recomm.iloc[:self.n][self.column_to_display])
        else:  # display all if # of recommendations is less than self.n
            print("Below is a list of all {} recommended restaurants for you: ".format(len(self.recomm)))
            print(self.recomm[self.column_to_display])
     
    #---------------------------------------------------------------
    # non-personalized keyword filtering-based recommender module
    def keyword(self, df=None, zipcode=None, city=None, state=None, max_distance=10, cuisine=None, style=None, price=None, personalized=False, original_score=False):
        """Non-personalized recommendation by keyword filtering: 
        Support filtering by the distance and location (zipcode, city, state) of interest, 
        by the desired cuisine, by the desired style, and by the desired price range. 
        The module supports multiple price range inputs separated by comma.
        ---
        Note:
        df: the default restaurant catalog is all the open restaurants in the 'business' dataset, 
            if a subset is prefered, e.g. previous filtered result, the subset can be passed via keyword argument 'df'
        state: needs to be the upper case of the state abbreviation, e.g.: 'NV', 'CA'
        max_distance: the max acceptable distance between the restaurant and the location of interest, unit is in miles, default is 10
        """
        
        # re-initiate the following variables every time the module is called so that the recommendation starts fresh
        self.recomm = df if df is not None else self.business[self.business.is_open ==1] # start with the desired restaurant catalog
        self.recomm['distance_to_interest'] = np.nan # reset the distance between each restaurant and the location of interest
        self.column_to_display = ['state','city','name','address','attributes.RestaurantsPriceRange2','cuisine','style','review_count','stars','adjusted_score'] # reset the columns to display
        self.original_score = original_score
        
        # assign variables based on user's keyword inputs
        self.zipcode, self.city, self.state, self.max_distance = zipcode, city, state, max_distance
        self.cuisine, self.style, self.price = cuisine, style, price
        
        # check self.module and column names to see a personalized score is available for ranking and displaying personalized recommendations
        if personalized:
            if (self.module == 0) or ('predicted_stars' not in self.recomm.columns and 'similarity_score' not in self.recomm.columns):
                print("no personalized list of recommendations is generated yet!")
                print("please first run the collaborative recommender module or content-based recommender module for a personalized recommendations.")
                return None
        
        # filter by restaurant location
        if (self.zipcode != None) or (self.city != None) or (self.state != None):      
            if (self.zipcode != None) or (self.city != None): # use zipcode and/or city whenever available
                self._filter_by_location()
            else: # filter by state if state is the only location information available 
                self._filter_by_state()
            if len(self.recomm) == 0:
                print("no restaurant found for the matching location of interest.")
                return None
        
        # filter by restaurant 'cuisine'
        if self.cuisine != None:
            self._filter_by_cuisine()
            if len(self.recomm) == 0:
                print("no restaurant found for the matching cuisine of {}".format(self.cuisine))
                return None
    
        # filter by restaurant 'style'
        if self.style != None:
            self._filter_by_style() 
            if len(self.recomm) == 0:
                print("no restaurant found for the matching style of {}".format(self.style))
                return None
        
        # filter by restaurant price range
        if self.price != None:
            self.price = [i.strip() for i in price.split(',')] #extract multiple inputs of price range
            self._filter_by_price()
            if len(self.recomm) == 0:
                print("no restaurant found for the matching price of {}".format(self.price))
                return None
        
        # sort the matching list of restaurants by the score of interest
        if personalized:
            if self.module == 1:
                score = 'predicted_stars'
                self.column_to_display.insert(0, 'predicted_stars')  # add 'predicted_stars' to the list of columns to display
            elif self.module == 2:
                score = 'similarity_score'
                self.column_to_display.insert(0, 'similarity_score')  # add 'similarity_score' to the list of columns to display
        elif self.original_score:  # set sorting criteria to the originial star rating
            score = 'stars'
        else:  # set sorting criteria to the adjusted score
            score = 'adjusted_score'
        self.recomm = self.recomm.sort_values(score, ascending=False)
        
        # display the list of top n recommendations
        self.display_recommendation()
        
        return self.recomm
    
    
    #------------------------------------------------------------
    # personalized collaborative recommender module
    def collaborative(self, user_id=None):
        """Personalized recommendation by collaborative filtering: 
        Recommendation is generated based on the predicted ratings from user x restaurant matrix factorization.
        ---
        note:
        Passing of user_id is required for the collaborative personalized module. If user's history is not available,
        a generic recommendation will be computed and returned based on all users' history in the database. 
        ---
        """
        
        self.user_id = user_id # user_id for personalized recommendation using collaborative module 
        if self.user_id is None:
            print("no user_id is provided!")
            return None
        if len(self.user_id) != 22:
            print("invalid user id!")
            return None
        
        # initiate every time the module is called
        self.recomm = self.business[self.business.is_open ==1] # start with all open restaurants from the entire 'business' catalog
        self.column_to_display = ['state','city','name','address','attributes.RestaurantsPriceRange2',\
                                  'cuisine','style','review_count','stars','adjusted_score'] # reset the columns to display
        if 'predicted_stars' in self.recomm.columns:
            self.recomm.drop('predicted_stars', axis=1, inplace=True) # delete the column of 'predicted_stars' if already present
        
        # extract all necessary information saved from the matrix factorization algorithm
        user_latent, item_latent = self.svd_trained_info['user_latent'], self.svd_trained_info['item_latent']
        user_bias, item_bias = self.svd_trained_info['user_bias'], self.svd_trained_info['item_bias']
        r_mean = self.svd_trained_info['mean_rating'] # global mean of all ratings
        userid_to_idx, itemid_to_idx = self.svd_trained_info['userid_to_index'], self.svd_trained_info['itemid_to_index']        
        
        # predict personalized restaurant ratings for the user_id of interest
        if self.user_id in userid_to_idx:
            u_idx = userid_to_idx[self.user_id]
            pred = r_mean + user_bias[u_idx] + item_bias + np.dot(user_latent[u_idx,:],item_latent.T)
        else: 
            print("sorry, no personal data available for this user_id yet!")
            print("Here is the generic recommendation computed from all the users in our database:")
            pred = r_mean + item_bias
        
        # pairing the predicted ratings with the business_id by matching the corresponding matrix indices of the business_id
        prediction = pd.DataFrame(data=pred, index=itemid_to_idx.values(), columns=['predicted_stars']) 
        assert len(prediction) == len(pred)
        prediction['business_id'] = list(itemid_to_idx.keys())
        
        # filter to unrated business_id only by the user_id of interest if a personal history is available
        if self.user_id in userid_to_idx:       
            busi_rated = self.review[self.review.user_id == self.user_id].business_id.unique()
            prediction = prediction[~prediction.business_id.isin(busi_rated)]
        
        # inner-join the prediction dataframe with the recommendation catalog on 'business_id' to retrieve all relevant business information
        # note: the .merge step needs to be performed prior to extracting the top n, because many businesses in 'review' dataset are not restaurant-related, therefore not present in 'business' dataset
        self.recomm = self.recomm.merge(prediction, on='business_id', how='inner') 
        
        # sort the prediction by the predicted ratings in descending order
        self.recomm = self.recomm.sort_values('predicted_stars', ascending=False).reset_index(drop=True)
        
        # add 'predicted_stars' to the list of columns to display and update self.module to 1
        self.column_to_display.insert(0, 'predicted_stars') 
        self.module = 1
        
        # display the list of top n recommendations
        self.display_recommendation()
        
        return self.recomm
    
    
    #------------------------------------------------------------
    # personalized content-based recommender module
    def content(self, user_id=None):
        """Personalized recommendation by content-based filtering based on restaurant reviews: 
        Recommendation is generated based on cosine similarity scores between user and restaurant feature vectors. 
        The feature vector space is extracted based on all the restaurant reviews.
        ---
        note:
        Passing of user_id is required for the content-based personalized module. 
        If user's history is not available, an empty dataframe will be returned along with a warning message. 
        ---
        """
        
        self.user_id = user_id # user_id for personalized recommendation using content-based module
        if self.user_id is None:
            print("no user_id is provided!")
            return None
        if len(self.user_id) != 22:
            print("invalid user id!")
            return None
        if self.user_id not in self.review_s.user_id.unique(): # check if previous restaurant rating/review history is available for the user_id of interest
            print("sorry, no personal data available for this user_id yet!")
            return None
        
        # initiate every time the module is called
        self.recomm = self.business[self.business.is_open ==1] # start with all open restaurants from the entire 'business' catalog
        self.column_to_display = ['state','city','name','address','attributes.RestaurantsPriceRange2',\
                                  'cuisine','style','review_count','stars','adjusted_score'] # reset the columns to display
        if 'similarity_score' in self.recomm.columns:
            self.recomm.drop('similarity_score', axis=1, inplace=True) # delete the column of 'cosine_similarity' if already present
        
        # predict personalized cosine similarity scores for the user_id of interest
        sim_matrix = linear_kernel(self.user_pcafeature.loc[user_id].values.reshape(1, -1), self.rest_pcafeature)
        sim_matrix = sim_matrix.flatten()
        sim_matrix = pd.Series(sim_matrix, index = self.rest_pcafeature.index)
        sim_matrix.name = 'similarity_score'
        
        # pairing the computed cosine similarity score with the business_id by matching the corresponding matrix indices of the business_id
        self.recomm = pd.concat([sim_matrix, self.recomm.set_index('business_id')], axis=1, join='inner').reset_index()
        
        # filter to unrated business_id only by the user_id of interest if a personal history is available      
        busi_rated = self.review_s[self.review_s.user_id == self.user_id].business_id.unique()
        self.recomm = self.recomm[~self.recomm.business_id.isin(busi_rated)]
               
        # sort the recommendation by the cosine similarity score in descending order
        self.recomm = self.recomm.sort_values('similarity_score', ascending=False).reset_index(drop=True)
           
        # add 'similarity_score' to the list of columns to display and update self.module to 2
        self.column_to_display.insert(0, 'similarity_score') 
        self.module = 2
        
        # display the list of top n recommendations
        self.display_recommendation()
        
        return self.recomm