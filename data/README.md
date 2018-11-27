**Raw Dataset:**<br>
The raw dataset is free and publicly available from Yelp website at https://www.yelp.com/dataset. 
Upon a quick and simple signup, five json files will be available for download: 
  1. 'business.json'
  2. 'user.json'
  3. 'review.json'
  4. 'tip.json'
  5. 'checkin.json'
Note: total size of the dataset is more than 7 Gb. 


**json-to-csv Conversion:**<br>
The raw json files can be converted to csv files using the 'json_to_csv.py' script provided in this repo: 
https://github.com/jingzhaomirror/Springboard_capstone_2/blob/master/json_to_csv.py
Nested json dictionaries are flatterned during this conversion and both parent and nested key, value pairs are extracted with column names of 'parentkey.childkey'. 


**Cleaned csv Files:**<br>
After converting from json to csv, data wrangling was performed and the cleaned csv files are saved. These cleaned files are available for download at: 
  1. 'business_clean.csv' https://drive.google.com/file/d/1gOD2V6qrjKi2eMLUJpeVm97GksgiwqmR/view?usp=sharing
  2. 'user_clean.csv'
  3. 'review_clean.csv'
  4. 'tip_clean.csv'
  5. 'checkin_clean.csv'
Please refer to the data wrangling notebook for the details on data wrangling: 


