#todo function to access owner and forces more easily

CONNECT = """
Alaska--Northwest Territories--Alberta--Alaska
Alberta--Ontario--Greenland--Northwest Territories
Greenland--Quebec--Ontario--Eastern United States--Quebec
Alberta--Western United States--Ontario--Northwest Territories
Western United States--Eastern United States--Mexico--Western United States

Venezuela--Peru--Argentina--Brazil
Peru--Brazil--Venezuela

North Africa--Egypt--East Africa--North Africa
North Africa--Congo--East Africa--South Africa--Congo
East Africa--Madagascar--South Africa

Indonesia--Western Australia--Eastern Australia--New Guinea--Indonesia
Western Australia--New Guinea

Iceland--Great Britain--Western Europe--Southern Europe--Northern Europe--Western Europe
Northern Europe--Great Britain--Scandinavia--Northern Europe--Ukraine--Scandinavia--Iceland
Southern Europe--Ukraine

Middle East--India--South East Asia--China--Mongolia--Japan--Kamchatka--Yakutsk--Irkutsk--Kamchatka--Mongolia--Irkutsk
Yakutsk--Siberia--Irkutsk
China--Siberia--Mongolia
Siberia--Ural--China--Afghanistan--Ural
Middle East--Afghanistan--India--China

Mexico--Venezuela
Brazil--North Africa
Western Europe--North Africa--Southern Europe--Egypt--Middle East--East Africa
Southern Europe--Middle East--Ukraine--Afghanistan--Ural
Ukraine--Ural
Greenland--Iceland
Alaska--Kamchatka
South East Asia--Indonesia
"""

CONNECTIONS = {'Alaska': ['Alberta', 'Northwest Territories', 'Kamchatka'],
               'Northwest Territories': ['Alberta', 'Greenland', 'Ontario', 'Alaska'],
               'Greenland': ['Quebec', 'Northwest Territories', 'Ontario', 'Iceland'],
               'Alberta': ['Western United States', 'Northwest Territories', 'Ontario', 'Alaska'],
               'Ontario': ['Alberta', 'Quebec', 'Eastern United States', 'Greenland', 'Northwest Territories',
                           'Western United States'], 'Quebec': ['Greenland', 'Ontario', 'Eastern United States'],
               'Western United States': ['Alberta', 'Mexico', 'Ontario', 'Eastern United States'],
               'Eastern United States': ['Quebec', 'Mexico', 'Ontario', 'Western United States'],
               'Mexico': ['Venezuela', 'Eastern United States', 'Western United States'],
               'Venezuela': ['Brazil', 'Mexico', 'Peru'], 'Brazil': ['North Africa', 'Venezuela', 'Argentina', 'Peru'],
               'Peru': ['Brazil', 'Venezuela', 'Argentina'], 'Argentina': ['Brazil', 'Peru'],
               'North Africa': ['East Africa', 'Egypt', 'Brazil', 'Southern Europe', 'Congo', 'Western Europe'],
               'Egypt': ['Middle East', 'Southern Europe', 'North Africa', 'East Africa'],
               'East Africa': ['North Africa', 'Madagascar', 'Egypt', 'South Africa', 'Middle East', 'Congo'],
               'Congo': ['North Africa', 'East Africa', 'South Africa'],
               'South Africa': ['Madagascar', 'East Africa', 'Congo'], 'Madagascar': ['East Africa', 'South Africa'],
               'Iceland': ['Greenland', 'Great Britain', 'Scandinavia'],
               'Great Britain': ['Scandinavia', 'Western Europe', 'Iceland', 'Northern Europe'],
               'Scandinavia': ['Ukraine', 'Great Britain', 'Iceland', 'Northern Europe'],
               'Ukraine': ['Afghanistan', 'Ural', 'Middle East', 'Southern Europe', 'Scandinavia', 'Northern Europe'],
               'Northern Europe': ['Ukraine', 'Great Britain', 'Southern Europe', 'Scandinavia', 'Western Europe'],
               'Western Europe': ['Great Britain', 'Southern Europe', 'North Africa', 'Northern Europe'],
               'Southern Europe': ['North Africa', 'Ukraine', 'Egypt', 'Middle East', 'Northern Europe',
                                   'Western Europe'],
               'Middle East': ['Afghanistan', 'East Africa', 'Egypt', 'Ukraine', 'India', 'Southern Europe'],
               'Afghanistan': ['Ukraine', 'India', 'Ural', 'China', 'Middle East'],
               'India': ['South East Asia', 'Middle East', 'Afghanistan', 'China'],
               'South East Asia': ['Indonesia', 'India', 'China'],
               'China': ['Afghanistan', 'South East Asia', 'Ural', 'India', 'Siberia', 'Mongolia'],
               'Mongolia': ['Kamchatka', 'China', 'Siberia', 'Japan', 'Irkutsk'], 'Japan': ['Mongolia', 'Kamchatka'],
               'Kamchatka': ['Alaska', 'Mongolia', 'Yakutsk', 'Japan', 'Irkutsk'],
               'Irkutsk': ['Mongolia', 'Siberia', 'Kamchatka', 'Yakutsk'],
               'Yakutsk': ['Siberia', 'Kamchatka', 'Irkutsk'],
               'Siberia': ['Ural', 'China', 'Mongolia', 'Yakutsk', 'Irkutsk'],
               'Ural': ['Ukraine', 'Siberia', 'Afghanistan', 'China'],
               'Indonesia': ['Western Australia', 'South East Asia', 'New Guinea'],
               'New Guinea': ['Western Australia', 'Indonesia', 'Eastern Australia'],
               'Eastern Australia': ['Western Australia', 'New Guinea'],
               'Western Australia': ['Indonesia', 'Eastern Australia', 'New Guinea']}

AREAS = {
    "North America": (5, ["Alaska", "Northwest Territories", "Greenland", "Alberta", "Ontario", "Quebec",
                          "Western United States", "Eastern United States", "Mexico"]),
    "South America": (2, ["Venezuela", "Brazil", "Peru", "Argentina"]),
    "Africa": (3, ["North Africa", "Egypt", "East Africa", "Congo", "South Africa", "Madagascar"]),
    "Europe": (
        5,
        ["Iceland", "Great Britain", "Scandinavia", "Ukraine", "Northern Europe", "Western Europe", "Southern Europe"]),
    "Asia": (7, ["Middle East", "Afghanistan", "India", "South East Asia", "China", "Mongolia", "Japan", "Kamchatka",
                 "Irkutsk", "Yakutsk", "Siberia", "Ural"]),
    "Australia": (2, ["Indonesia", "New Guinea", "Eastern Australia", "Western Australia"])
}

AREA_TERRITORIES = {key: value[1] for (key, value) in AREAS.items()}

MAP = """
  aa       bbbb b         cccccc          pp     tB B BCCCCCDDDDDDDDFFFF       
 aaaaaaabbbbbbbbbb        cccc           ppptt tttBBBBBCCCCCDDDDDDDFFFFFFFFFFF 
 aaaaaaabbbbbbbbbbb       ccc   nnn     pp pttttttBBBBBCCCCCDDDDDFFFFFFFFFFFF F
 aaaaaaaaddddddde   fff    c        o  pp  tttttttBBBBBCCCEEEEEEEFFFFFFFFFF    
  a     adddddddeee  fff           oo   p rtttttttBBBBBCCEEEEEEEEFFF    F      
        adddddddeeeefffff          ooo rrrrtttttGGGGBBBCCEEEEHHHHHFFF          
          ddddddeeeeffff f           qqrrrrtttttGGGGGGBIIIIHHHHHHHHH           
          ggggggghh ffff             qqsssss ttt GGGGGGIIIIIHHHHHHHH           
          ggggggghhhhh             qqq ss ss tt  GGGGGGIIIIIIIIIII  J          
           gggggghhhh              qq   s ssAAAAAAKKKGGIIIIIIIII I JJ          
           gggghhhhhh               uuuu     AAAAAKKKKKKIIIIIIII  JJ           
            ggghhh h               uuuuuuvvvvAAA AKKKKKKKIIIIIII  J            
              ii                  uuuuuuuvvvv AAAA  KKKKKKLLLLII               
              ii                  uuuuuuuvvvvv AAA   KKKK LLLL                 
               iii                uuuuuuuuwwww AA     KK  LLL                  
                  iiijj           uuuuuuuuwwwww       K     L   M              
                    jjjjj          uuuuuuxxwwwww       K   M   MM  NN          
                    kjjjmmmm            uxxwww              MMMM  NNNN          
                    kkmmmmmmmm          xxxwww                       N         
                     kkkmmmmm           xxxyyy zz                PPPP          
                      lkkmmmm           yyyyy  z               OOPPPPP         
                      lllll              yyyy  z              OOOOOPPPP        
                      llll               yyy                   OOOOPPPP        
                      lll                yy                    OO  PPPP        
"""
KEY = {
    "a": "Alaska",
    "b": "Northwest Territories",
    "c": "Greenland",
    "d": "Alberta",
    "e": "Ontario",
    "f": "Quebec",
    "g": "Western United States",
    "h": "Eastern United States",
    "i": "Mexico",
    "j": "Venezuela",
    "k": "Peru",
    "l": "Argentina",
    "m": "Brazil",
    "n": "Iceland",
    "o": "Great Britain",
    "p": "Scandinavia",
    "q": "Western Europe",
    "r": "Northern Europe",
    "s": "Southern Europe",
    "t": "Ukraine",
    "u": "North Africa",
    "v": "Egypt",
    "w": "East Africa",
    "x": "Congo",
    "y": "South Africa",
    "z": "Madagascar",
    "A": "Middle East",
    "B": "Ural",
    "C": "Siberia",
    "D": "Yakutsk",
    "E": "Irkutsk",
    "F": "Kamchatka",
    "G": "Afghanistan",
    "H": "Mongolia",
    "I": "China",
    "J": "Japan",
    "K": "India",
    "L": "South East Asia",
    "M": "Indonesia",
    "N": "New Guinea",
    "O": "Western Australia",
    "P": "Eastern Australia",
}


# todo improve
class World(object):

    def __init__(self, copy=None):
        if copy is None:
            self.owners = dict({name: None for name in KEY.values()})
            self.forces = dict({name: 0 for name in KEY.values()})
            #todo class attribute
            self.connections = CONNECTIONS.copy()
            self.areas = AREA_TERRITORIES.copy()
            self.area_values = dict({key: value[0] for (key, value) in AREAS.items()})
        else:
            #todo check
            self.owners = copy.owners.copy()
            self.forces = copy.forces.copy()
            self.connections = CONNECTIONS.copy()
            self.areas = AREA_TERRITORIES.copy()
            self.area_values = dict({key: value[0] for (key, value) in AREAS.items()})

    def copy(self):
        return World(self)
