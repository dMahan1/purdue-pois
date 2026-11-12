# Purdue POIs
Page to find nearby points of interest around campus

Uses the Python-Django stack

**Running the Program**

```sh
cd django
python3 -m pip install django
python3 manage.py migrate
python3 manage.py runserver
```
**AI Usage**

Claude was used in the development of this program.

I used Claude to:
- Scaffold the site as I have never used Django in the past and needed a good foundation
- Code a well working HTML frontend that can connect intuitively to the Python-Django backend
- Advise in functions architecture of the program (i.e. How best to structure the Event form to make it easier to use in searching, creation, and editing)
- Create example data
- Write tests
- Create functions to calculate Haversine Distance to lat-longs (Originally my plan was to just include the building in event data, but I wanted to be able to sort and query by distance to your location, and I haven't used these calculations before)

All AI generated code was reviewed and several design choices in the HTML, example data, search query assumptions, and function choices were altered by me either for user convenience, correctness, or as a deliberate design choice. (For example, Claude suggested example ranges of distance when writing the haversine code that were far too large for campus-only searches, and those were corrected. Also, Claude tried to get me to add Indexing into the program, but I decided against that at this point as it is a large section of Part 3 of this project and is unneccesary at this point)

