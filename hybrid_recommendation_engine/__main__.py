# -*- coding: utf-8 -*-
"""
User interface for the hybrid recommendation engine:
Created on Tue Jan 15 10:50:00 2019 @author: jingzhao

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

import sys
from recommender import Recommender

# welcome message
print("Hey, welcome to the Hybrid Yelp Recommender!")
print("Please wait while we initiate the recommendation engine\n loading...")

# initiation
boolean = True
personalized = False
original_score = False
n = 5
recommender = Recommender(personalized=True) # initiate the recommender object
print("Yeah, recommendation engine is ready to use!")      
    
# def nested function for obtaining user keywords for filtering the recommendations
def _getkeywords():
    # initiate
    zipcode, city, state = None, None, None
    max_distance = 10
    cuisine, style, price = None, None, None
    # list of supporting cuisines and styles
    cuisines = ['mexican','italian','chinese','japanese','thai','indian','american (new)','american (traditional)',\
                'french','middle eastern','korean','mediterranean','vietnamese','cajun','greek','hawaiian',\
                'asian fusion','vegetarian','vegan','steakhouse','barbeque','sushi bars','tex-mex','specialty food',\
                'gluten-free','coffee & tea','desserts','seafood','ice cream & frozen yogurt','bakeries','beer',\
                'wine & spirits','soup','pizza','hot dogs','burgers','donuts','cupcakes','salad','tacos',\
                'chicken wings','sandwiches','bubble tea','tapas/small plates','shaved ice','bagels','southern',\
                'local flavor','latin american','custom cakes','ethinic food']
    styles = ['restaurants','fast food','food stands','street vendors','nightlife','buffets','bars','food trucks',\
              'breakfast & brunch','diners','cocktail bars','pubs','sports bars','wine bars','beer bars',\
              'casinos','juice bars & smoothies','caterers','delis','cafes','lounges','music venues',\
              'performing arts','food delivery services','dive bars','dance clubs','breweries']

    r = input("What would you like to filter by? \n1 location (zipcode, city, state);\n2 cuisine;\n3 style;\n4 price range\nPlease enter the corresponding numbers. Multiple filtering criteria are supported, please separate the corresponding numbers by comma.\n")
    if len(r) > 0:
        print("Great! Now let's gather your filtering criteria.")
        kws = r.split(',')
        for kw in kws:
            try:
                kw = int(kw)
            except:
                print("Ooops, invalid input of '{}' skipped".format(kw))
                continue
            if kw == 1:
                print("Please follow the instructions to enter your location of interest or use the ENTER/RETURN key to skip.")
                r = input("Please enter the zipcode of interest or use the ENTER/RETURN key to skip\n")
                if len(r) > 0:
                    zipcode = r
                r = input("Please enter the city of interest or use the ENTER/RETURN key to skip\n")
                if len(r) > 0:
                    city = r
                r = input("Please enter the state of interest or use the ENTER/RETURN key to skip\n")
                if len(r) > 0:
                    state = r
                r = input("Please enter the max distance allowed between the restaurant and your location of interest or use the ENTER/RETURN key to skip\n")
                if len(r) > 0:
                    try:
                        max_distance = int(r)
                    except:
                        print("Ooops, invalid number! The max distance is set to the default 10 miles.")                                
            elif kw == 2: 
                while True:
                    r = input("Please select one from the following cuisines as your interest or use the ENTER/RETURN key to skip:\n{}\n".format(cuisines))
                    if len(r) > 0:
                        if r in cuisines:
                            cuisine = r
                            break
                        else:
                            print("Ooops, invalid cuisine!")
                    else:
                        break
            elif kw == 3:
                while True:
                    r = input("Please select one from the following styles as your interest or use the ENTER/RETURN key to skip:\n{}\n".format(styles))
                    if len(r) > 0:
                        if r in styles:
                            style = r
                            break
                        else:
                            print("Ooops, invalid style!")
                    else:
                        break
            elif kw == 4:
                r = input("Please indicate your price range of interest: \n1 cheap ($);\n2 medium ($$);\n3 expensive ($$$);\n4 most expensive($$$$)\nPlease enter the corresponding number(s) separated by comma\n")
                if len(r) > 0:
                    price = r
            else:
                print("Ooops, invalid category of '{}' skipped".format(kw))
    return zipcode, city, state, max_distance, cuisine, style, price
    
# main user interface for the recommendation engine
while boolean:
        
    r = input("Want to try a customized recommendation based on your Yelp user history? yes/no\n")   
    if r.startswith('Y') or r.startswith('y'):
        personalized = True   
        
    # personalized recommender modules
    if personalized: 
        print("Awesome! Let's start your personalized recommendation.")
        # obtain user id
        r = input("To retrieve your user history, please enter your Yelp User ID (length of 22 characters):\n")
        if len(r) == 0:
            print("Ooops, no user id is provided! Let's give it another try.")
            continue
        elif len(r) != 22:
            print("Ooops, it seems to be an invalid user id! Let's give it another try.")
            continue
        else:
            user_id = r
            print("Great! Valid user id fetched! Just one more question before generating your recommendations")
            # decide which personalized recom
            r = input("Which personalized recommendation would you prefer? \n1. Something new based on people like you; \n2. Something similar to your favorate restaurants; \nPlease enter 1 or 2\n")
            try: 
                r = int(r)
                if r not in [1,2]:
                    print("Ooops, invalid input! Let's give it another try.")
                    continue
                else:
                    print("Awesome, All set! Here is your personalized recommendations:\n")
                    if r == 1: 
                        print("---------")
                        result = recommender.collaborative(user_id=user_id)
                        print("---------")
                    else:
                        print("---------")
                        result = recommender.content(user_id=user_id)
                        print("---------")
            except:
                print("Ooops, invalid input! Let's give it another try.")
                continue
                    
    # non-personalized recommender module
    else: 
        print("That's cool! Let's filter by keywords and generate your recommendations!")
        zipcode, city, state, max_distance, cuisine, style, price = _getkeywords()
        print("Great! Filtering criteria fetched! Just one more question before generating your recommendations")
        r = input("Wanna rank your recommendations by 'smart' ratings?\n'smart' rating adjusts the original restaurnat average star rating by the number of ratings it receives.\nEnter no to deactivate smart ratings or any other key to continue\n")
        if r.startswith('N') or r.startswith('n'):
            original_score = True
        print("Awesome, all set! Here is your recommendations:\n")
        print("---------")
        result = recommender.keyword(zipcode=zipcode, city=city, state=state, max_distance=max_distance, cuisine=cuisine, style=style, price=price, original_score=original_score)
        print("---------")
            
    # refine recommendation results
    if result is not None and len(result) > 0:
        r = input("Would you like to display more/less recommendation results? Enter the desire number to continue or any other key to skip:\n")
        try:
            n = int(r)
            print("---------")
            recommender.display_recommendation(n=n)
            print("---------")
        except:
            pass
        r = input("Would you like to further filter your recommendation results by keywords? Enter yes to continue or any other key to skip:\n")
        if r.startswith('Y') or r.startswith('y'):
            zipcode, city, state, max_distance, cuisine, style, price = _getkeywords()
            print("---------")
            result = recommender.keyword(df=result, zipcode=zipcode, city=city, state=state, max_distance=max_distance, cuisine=cuisine, style=style, price=price, personalized=personalized)
            print("---------")
                
    # quit or restart the recommendation engine
    print("Awesome, all done!")
    r = input("Please enter q to quit the recommendation engine, or enter c to restart with another recommendation\n")
    if len(r) == 0 or r.startswith('Q') or r.startswith('q'):
        boolean = False
        print("Enjoy your recommendations! See you next time!")

sys.exit()