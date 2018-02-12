import pandas
import folium
import csv
import random
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import ArcGIS


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

    high_limit = 150
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
        geolocator = ArcGIS()
        loc = geolocator.geocode(loc_name)
        if loc.latitude:
            return (loc.latitude, loc.longitude)
        else:
            if loc_name.find(',') != -1:
                return get_coordinates(loc_name[loc_name.find(',') + 2:])
            else:
                return (None, None)

    def get_location(loc):
        """
        (str) -> [(float, float), str, str]
        Returns list of coordinates
        and name of location.

        >>> get_location('"13mil" (2015) {Deborah (#1.5)}' \
        + '				Barcelona, Catalonia, Spain')
        [(41.38561000000004, 2.1687200000000644), 'Barcelona, Catalonia, Spain', '"13mil"']
        >>> get_location('"2091" (2016) {Caballo de '\
        + 'Troya (#1.4)}			Tatacoa Desert, Colombia	(location)')
        [(3.2587800000000584, -75.14029999999997), 'Tatacoa Desert, Colombia', '"2091"']
        """
        if loc.endswith('\n'):
            loc = loc[:-1]
        # Name of film
        name = (loc[:loc.find('(')]).strip()
        loc = loc.split('\t')
        # Removes some additional information, like '(studio)'
        if loc[-1][0] == '(':
            loc = loc[-2]
        else:
            loc = loc[-1]
        return [get_coordinates(loc), loc, name]

    locations = dict()
    #print(get_location('"2091" (2016) {Caballo de '\
    #    + 'Troya (#1.4)}			Tatacoa Desert, Colombia	(location)'))
    for line in lines:
        while True:
            try:
                movie_loc = get_location(line)
                break
            except GeocoderTimedOut:
                print("Something gone wrong...")
                print(line)
        coordinates = movie_loc[0]
        # This location has founded
        if coordinates[0]:
            # Increase number of created films to this location
            if coordinates in locations:
                # Increase number of films in this location
                locations[coordinates][1] += 1
                # Add name of film in this location
                locations[coordinates].append(movie_loc[2])
            else:
                # value: name of location, 1
                locations[coordinates] = [movie_loc[1], 1, movie_loc[2]]
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
                         'latitude', 'longitude', 'Names of films'])
        # Write each location in csv file
        for coordinates, loc_info in dict_loc.items():
            # Name of loc, number of films in this loc,
            # latitude, longitude, names of films
            lst = [loc_info[0], loc_info[1],
                   coordinates[0], coordinates[1], loc_info[2]]
            writer.writerow(lst)
        # Close and save csv file
        csvfile.close()


def make_html_map(path, year):
    """
    (str, int) -> (file)
    Creates html file with map of films.
    Gets data about locations from path.
    """
    def color_creator(films_num):
        """
        (int) -> (str)
        Returns name of color for circle marker,
        depends on number of films in this location.
        """
        if films_num == 1:
            return "green"
        elif 2 <= films_num <= 4:
            return "blue"
        else:
            return "purple"

    def color_population(popul):
        """
        (int) -> (str)
        Returns name of color for filling area,
        depends on number of population.
        """
        popul = popul['properties']['POP2005']
        if popul < 10000000:
            return {'fillColor': 'green'}
        elif 10000000 <= popul < 20000000:
            return {'fillColor': 'orange'}
        else:
            return {'fillColor': 'red'}

    map = folium.Map(zoom_start=3)
    folium.TileLayer('stamentoner').add_to(map)
    data = pandas.read_csv(path)
    lat = data['latitude']
    lon = data['longitude']
    num = data['Number of films in this location']
    names = data['Names of films']
    loc_layer = folium.FeatureGroup(name="Locations of films")
    for nm, lt, ln, mov in zip(num, lat, lon, names):
        loc_layer.add_child(folium.CircleMarker(location=[lt, ln],
                                                radius=3,
                                                # Number of films
                                                popup=str(nm),
                                                fill_color='white',
                                                color=color_creator(nm),
                                                fill_opacity=1))

    fg_pp = folium.FeatureGroup(name="Population")
    fg_pp.add_child(folium.GeoJson(data=open('world1.json', 'r',
                                             encoding='utf-8-sig').read(),
                                   style_function=color_population))
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


if __name__ == "__main__":
    import time
    year_test = input_year()
    st = time.time()

    while True:
        # Maybe, for creating map, in folder are additional files
        try:
            make_html_map('films_{}.csv'.format(year_test), year_test)
            break
        except FileNotFoundError:
            data = read_data('locations.list.txt')
            # File with data have founded
            if data:
                # Process data, create additional file for creating map
                data = list_lines_year(data, year_test)
                dict_movi = dict_films(data)
                location_csv_file(dict_movi, year_test)
            else:
                break

    fn = time.time()
    print("This process continued {} seconds.".format(fn - st))
