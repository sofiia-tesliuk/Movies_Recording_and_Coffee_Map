import pandas
import folium
import geocoder
import csv
import random
from geopy.geocoders import Nominatim


def read_data(path):
    """
    (str) -> (list)
    Reads content from path and returns list of lines of path.
    """
    try:
        with open(path, 'r', encoding='UTF-8', errors='ignore') as file:
            lines = file.readlines()
            # Needed information is after 15-th line
            return lines[15:]
    except FileNotFoundError:
        print('There is no file with such name.')
    except IndexError:
        print('In this file too less information about locations.')


def list_lines_year(lines, year):
    """
    (lst, int) -> (lst)
    Returns list with lines of films,
    created in entered year.
    But if there too many lines (more than 500), it returns
    500 randomly choised lines in case of to not burden the map.
    """
    def same_year(line, year):
        """
        (str, str) -> (bool)
        Returns if year, mentioned in line, is the same as needed.

        >>> same_year('"2091" (2016) {Caballo de Troya (#1.4)}'\
        + '			Tatacoa Desert, Colombia	(location)', '2016')
        True
        >>> same_year('"2091" (2016) {Caballo de Troya (#1.4)}'\
        + '			Tatacoa Desert, Colombia	(location)', '2091')
        False
        """
        index = 0
        while True:
            index = line.find(year, index + 1)
            if index > 0:
                # This year is exactly year of creating,
                # not in film name or location
                if line[index - 1] == '(':
                    return True
            else:
                return False

    lines_year = []
    year = str(year)
    for line in lines:
        # If year of current film in line is the same as entered year
        if same_year(line, year):
            lines_year.append(line)

    high_limit = 500
    if len(lines_year) > high_limit:
        lines_year = random.sample(lines_year, high_limit)
    return lines_year


def dict_films(lines):
    """
    (lst) -> (dict)
    Returns dict of coordinates as key,
    [name of location, number of films] as value.
    """
    def get_coordinates(loc_name):
        """
        (str) -> (float, float)
        Returns coordinates (latitude, longitude) of location.
        """
        loc = geocoder.google(loc_name)
        if not loc.lat:
            loc = geolocator.geocode(loc_name)
            if loc:
                # print("google:\t", repr(loc_name))
                return (loc.latitude, loc.longitude)
            else:
                # print("geopy: \t", repr(loc_name))
                if loc_name.find(',') != -1:
                    return get_coordinates(loc_name[loc_name.find(',') + 2:])
                else:
                    return (None, None)
        else:
            return (loc.lat, loc.lng)

    def get_location(loc):
        """
        (str) -> [(float, float), str]
        Returns list of coordinates
        and name of location.

        >>> get_location('"13mil" (2015) {Deborah (#1.5)}' \
        + '				Barcelona, Catalonia, Spain')
        ('13mil', 'Barcelona, Catalonia, Spain'), 'Spain'
        >>> get_location('"2091" (2016) {Caballo de '\
        + 'Troya (#1.4)}			Tatacoa Desert, Colombia	(location)')
        'Tatacoa Desert, Colombia'
        """
        if loc.endswith('\n'):
            loc = loc[:-1]
        loc = loc.split('\t')
        # Removes some additional information, like '(studio)'
        if loc[-1][0] == '(':
            loc = loc[-2]
        else:
            loc = loc[-1]
        return [get_coordinates(loc), loc]

    geolocator = Nominatim()
    locations = dict()
    for line in lines:
        movie_loc = get_location(line)
        coordinates = movie_loc[0]
        # This location has founded
        if coordinates[0]:
            # Increase number of created films to this location
            if coordinates in locations:
                locations[coordinates][1] += 1
            else:
                # value: name of location, 1
                locations[coordinates] = [movie_loc[1], 1]
    return locations


def location_csv_file(dict_loc, year):
    """
    (dict) -> (file)
    Creates csv file with coordinates of locations and additional information
    into csv file.
    """
    with open('films_{}.csv'.format(str(year)), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        # Write first line with term of each column
        writer.writerow(['Name of location', 'Number of films in this location',
                         'latitude', 'longitude'])
        # Write each location in csv file
        for coordinates, loc_info in dict_loc.items():
            # Name of loc, number of films in this loc, latitude, longitude
            lst = [loc_info[0], loc_info[1], coordinates[0], coordinates[1]]
            writer.writerow(lst)
        # Close and save csv file
        csvfile.close()


def make_html_map(path, year):
    """
    (str, int) -> (file)
    Creates html file with map of films.
    Gets data about locations from path.
    """
    map = folium.Map(zoom_start = 2.5)
    data = pandas.read_csv(path)
    lat = data['lat']
    lon = data['lon']
    num = data['Number of films in this location']

    loc_layer = folium.FeatureGroup(name=" locations_of_films ")
    for nm, lt, ln in zip(num, lat, lon):
        loc_layer.add_child(folium.Marker(location=[lt, ln],
                                          popup=nm,
                                          icon=folium.Icon()))

    fg_pp = folium.FeatureGroup(name="Population")
    fg_pp.add_child(folium.GeoJson(data=open('world.json', 'r',
                                             encoding='utf-8-sig').read(),
                                   style_function=lambda x: {'fillColor': 'green'
                                   if x['properties']['POP2005'] < 10000000
                                   else 'orange' if 10000000 <= x['properties']['POP2005'] < 20000000
                                   else 'red'}))
    map.add_child(fg_pp)
    map.add_child(loc_layer)
    map.add_child(folium.LayerControl())
    map.save("Map_{}.html".format(year))


def input_year():
    """
    () -> (int)
    Returns entered from console year.
    """
    try:
        year = int(input("Enter year: "))
        assert year > 0
        return year
    except:
        print("Please, enter positive integer.")
        input_year()


# -------------------------
# Other useful functions
# -------------------------

if __name__ == "__main__":
    year_test = 1895
    data = list_lines_year(read_data('locations.list.txt'), year_test)
    print("Get gata about films")
    dict_movi = dict_films(data)
    print("Proccesed data")
    location_csv_file(dict_movi, year_test)
    print("Created csv file")
    #make_html_map('films_{}.csv'.format(year_test), year_test)
    #print("Created html file")
