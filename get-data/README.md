## MongoDB Structure

### Collections
Database is named ```nhl```.

The active collections it contains are:

```
nhl.schedule
```

#### ```nhl.schedule```
This collection contains game information on a team by team basis.
Documents are identified by the three letter acronymn of the given team (lowercase).
Each document then contains a dictionary that maps the season to a list of games.
Each game is a dictionary with various fields.

For example, the document for the Toronto Maple Leafs could look something like this:
```
{'tor': {'20192020': [{game1}, {game2},...,{game90}], 
         '20182019': [{game1}, {game2},...,{game90}]
        }
```
