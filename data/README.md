**Raw dataset:**<br>
The raw dataset is free and publicly available from Yelp website at https://www.yelp.com/dataset. 
Upon a quick and simple signup, five json files will be available for download: 
  1. 'business.json'
  2. 'user.json'
  3. 'review.json'
  4. 'tip.json'
  5. 'checkin.json'
Note: total size of the dataset is more than 7 Gb. 


**json to csv conversion:**<br>
The raw json files can be converted to csv files using the 'json_to_csv.py' script provided in this repo: 

Nested json dictionaries are flatterned during this conversion and both parent and nested key, value pairs are extracted with column names of 'parentkey.childkey'. 


**cleaned csv files:**<br>
After converting from json to csv, data wrangling was performed and the cleaned csv files are saved. These cleaned files are available for download at: 

Please refer to the data wrangling notebook for the details on data wrangling: 

