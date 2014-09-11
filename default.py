'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

'''
    Random Movie script
    by elParaguayo

    Plays random movie from user's video library.

    Version: 0.1.0
'''

import sys
import random

if sys.version_info >=  (2, 7):
    import json as json
else:
    import simplejson as json

import xbmc
import xbmcgui
import xbmcaddon

_A_ = xbmcaddon.Addon()
_S_ = _A_.getSetting

# let's parse arguments before we start
try:
    # parse sys.argv for params
    params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
except:
    # no params passed
    params = {}
# set our preferences
filterGenres = params.get("filtergenre", "").lower() == "true"

# The filter by genre prompt can be set via the skin...
skinprompt = params.get("prompt", "").lower() == "true"

# ... or via the script settings
scriptprompt = _S_("promptGenre") == "true"

# If the skin setting is set to true this overrides the script setting
promptUser = skinprompt or scriptprompt

def localise(id):
    '''Gets localised string.

    Shamelessly copied from service.xbmc.versioncheck
    '''
    string = _A_.getLocalizedString(id).encode( 'utf-8', 'ignore' )
    return string

def getMovieLibrary():
    '''Gets the user's full video library.

    Returns dictionary object containing movies.'''

    # Build our JSON query
    jsondict = {"jsonrpc": "2.0",
                "method": "VideoLibrary.GetMovies",
                "params": {"properties": ["genre", "playcount", "file"]},
                "id": 1}

    # Submit our JSON request and get the response
    moviestring = unicode(xbmc.executeJSONRPC(json.dumps(jsondict)), 
                          errors='ignore')
    
    # Convert the response string into a python dictionary
    movies = json.loads(moviestring)


    # Return the "movies" part of the response, or None if no movies found
    return movies["result"].get("movies", None)

def getRandomMovie(filterWatched, filterGenre, genre=None):
    '''Takes the user's video library, filters it by the criteria
       requested by the user and then selects a random movie from the filtered 
       list.

       Returns the filepath of the random movie.
    '''

    # set up empty list for movies that meet our criteria
    movieList = []

    # loop through all movies
    # moviesJSON is global variable, it's not being modified
    for movie in moviesJSON:

        # reset the criteria flag
        meetsCriteria = False

        # Is the selected genre in the movie's list of genres?
        genrematch = genre in movie["genre"]
        
        # Is the movie currently unwatched?
        isUnwatched = movie["playcount"] == 0 

        # Test the movie against the criteria

        # If we are filtering both by genre and watched status...
        if filterGenre and filterWatched:

            # ...we need both of these to be True
            meetsCriteria = genrematch and isUnwatched

        # If we're just filtering by genre...
        elif filterGenre:

            # ... only this needs to be True
            meetsCriteria = genrematch

        # If we're fitering by watched status...
        elif filterWatched:

            # ... only this one needs to be True
            meetsCriteria = isUnwatched

        # And if we're not filtering by either...
        else:

            # ... we can add it to our list!
            meetsCriteria = True

        # If the film passes the tests... 
        if meetsCriteria:

            # ... let's add the filepath to our list.
            movieList.append(movie["file"])
    
    # return a random movie filepath
    try:
        return random.choice(movieList)

    # Will be empty if no results
    except IndexError:

        return None
    
def selectGenre(filterWatched):
    '''Displays a dialog of the genres of all movies in the user's library and 
       asks the user to select one.

       Parameters:

       filterWatched: restrict results to genres of unwatched movies.

       Returns:
       selectedGenre: string containing genre name or None if no choice made.
    '''
    # Empty list for holding genres
    myGenres = []
    selectedGenre = None
    
    # Loop through our movie library
    for movie in moviesJSON:

        # Let's get the movie genres
        # If we're only looking at unwatched movies then restrict list to 
        # those movies
        if (filterWatched and movie["playcount"] == 0) or not filterWatched:
            
            # Loop through genres for the current movie
            for genre in movie["genre"]:

                # Check if the genre is a duplicate
                if not genre in myGenres:

                    # If not, add it to our list
                    myGenres.append(genre)
    
    # Sort the list alphabetically                
    mySortedGenres = sorted(myGenres)

    # Prompt user to select genre
    selectGenre = xbmcgui.Dialog().select(localise(32024), mySortedGenres)
    
    # Check whether user cancelled selection
    if not selectGenre == -1:
        # get the user's chosen genre
        selectedGenre = mySortedGenres[selectGenre]
        
    # Return the genre (or None if no choice)
    return selectedGenre
    
    
def getUserPreference(title, message):
    '''Asks the user whether they want to restrict results.

       Returns:
       True:    Script should restrict films
       False:   Script can pick any film
    '''

    # Ask user whether they want to restrict selection
    a = xbmcgui.Dialog().yesno(title, 
                               message)
    
    # Deal with the output
    if a == 1: 
        
        # User wants restriction
        return True

    else:

        # No restriction needed
        return False
    
# get the full list of movies from the user's library
moviesJSON = getMovieLibrary()
    
# ask user if they want to only play unwatched movies    
unwatched = getUserPreference(localise(32021), localise(32022))  

# is skin configured to use one entry?
if promptUser and not filterGenres:

    # if so, we need to ask whether they want to select genre
    filterGenres = getUserPreference(localise(32023), localise(32024))  

# did user ask to select genre?
if filterGenres:

    # bring up genre dialog
    selectedGenre = selectGenre(unwatched)

    # if not aborted
    if selectedGenre:

        # get the random movie...
        randomMovie = getRandomMovie(unwatched, True, selectedGenre)

    else:

        # User cancelled so there's no movie to play
        randomMovie = None

else:
    # no genre filter
    # get the random movie...
    randomMovie = getRandomMovie(unwatched, False)

if randomMovie:

   # Play the movie 
    xbmc.executebuiltin('PlayMedia(' + randomMovie + ',0,noresume)')

else:

    # No results found, best let the user know
    xbmc.executebuiltin('Notification(%s,%s,2000)' % (localise(32025),
                                                      localise(32026)))
