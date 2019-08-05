import warnings
warnings.filterwarnings('ignore')

from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
from pandas.io.json import json_normalize
from itertools import compress
import re
from rdflib import Graph, Namespace, URIRef,Literal
from rdflib.namespace import RDF, FOAF, RDFS, XSD
def query_wikidata(sparql_query, sparql_service_url):
    # create the connection to the endpoint
    sparql = SPARQLWrapper(sparql_service_url)
    sparql.setTimeout(timeout=300)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    result = sparql.query().convert()
    return json_normalize(result["results"]["bindings"])

sparql_query="""        
        PREFIX dbc: <http://dbpedia.org/resource/Category:>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dct: <http://purl.org/dc/terms/>
        PREFIX dbo: <http://dbpedia.org/ontology/>

        SELECT DISTINCT ?arte ?artewiki ?sommario ?name (AVG(?lat) as ?lat) (AVG(?long) as ?long) (SAMPLE(?city) as ?city)
        ?cityUri (AVG(?city_lat) as ?city_lat) (AVG(?city_long) as ?city_long) ?image
        ?museum (SAMPLE(?museumlabel) as ?museumlabel)
         ?museumwiki ?sommario_museum (AVG(?museum_lat) as ?museum_lat) (AVG( ?museum_long) as  ?museum_long) WHERE{

         ?arte rdf:type dbo:Artwork;
               foaf:name ?name.
         OPTIONAL{
              ?arte dbp:city ?cityUri.
              FILTER(!(isLiteral(?cityUri))).
              OPTIONAL{
                   ?cityUri rdfs:label ?city.
                   filter langMatches(lang(?city), "en")
              }
              OPTIONAL{
                 ?cityUri dbp:latitude ?city_lat1;
                          dbp:longitude ?city_long1.
                 FILTER (datatype(?city_lat1) = xsd:float && datatype(?city_long1) = xsd:float) 
              }
              OPTIONAL{
                  ?cityUri geo:lat  ?city_lat2;
                           geo:long ?city_long2.
                  FILTER (datatype(?city_lat2) = xsd:float && datatype(?city_long2) = xsd:float) 
              }
         }
         OPTIONAL{
             ?arte dbo:abstract ?sommario1.
             FILTER langMatches(lang(?sommario1), "it")
         }
         OPTIONAL{
             ?arte dbo:abstract ?sommario2.
             FILTER langMatches(lang(?sommario2), "en")
         }
         OPTIONAL{
             ?arte dbp:latitude ?lat1;
                   dbp:longitude ?long1.
             FILTER (datatype(?lat1) = xsd:float && datatype(?long1) = xsd:float) 
         }
         OPTIONAL{
             ?arte geo:lat  ?lat2;
                   geo:long ?long2.
             FILTER (datatype(?lat2) = xsd:float && datatype(?long2) = xsd:float) 
         }

         OPTIONAL{
             ?arte dbo:museum ?museum.
             FILTER(!isLiteral(?museum)).
             OPTIONAL{
                 ?museum rdfs:label ?museumlabel.
                 FILTER langMatches(lang(?museumlabel),"en")
             }
             OPTIONAL{
                 ?museum foaf:isPrimaryTopicOf ?museumwiki.
             }
             OPTIONAL{
                 ?museum dbp:latitude ?museum_lat1;
                         dbp:longitude ?museum_long1.
                 FILTER(!isLiteral(?museum) && datatype(?museum_lat1) = xsd:float && datatype(?museum_long1) = xsd:float) 
             }
             OPTIONAL{
                 ?museum geo:lat ?museum_lat2;
                         geo:long ?museum_long2.
                 FILTER(!isLiteral(?museum) && datatype(?museum_lat2) = xsd:float && datatype(?museum_long2) = xsd:float) 
             }
             OPTIONAL{
                 ?museum dbo:abstract ?sommario_museum1.
                 FILTER langMatches(lang(?sommario_museum1), "it")
             }
             OPTIONAL{
                 ?museum dbo:abstract ?sommario_museum2.
                 FILTER langMatches(lang(?sommario_museum2), "en")
             }
         }
         OPTIONAL{
             ?arte foaf:isPrimaryTopicOf ?artewiki.
         }

         OPTIONAL{
             ?arte foaf:depiction ?image.
         }

         BIND(COALESCE(?lat1,?lat2) AS ?lat)
         BIND(COALESCE(?long1,?long2) AS ?long)

         BIND(COALESCE(?city_lat1,?city_lat2) AS ?city_lat)
         BIND(COALESCE(?city_long1,?city_long2) AS ?city_long)

         BIND(COALESCE(?museum_lat1,?museum_lat2) AS ?museum_lat)
         BIND(COALESCE(?museum_long1,?museum_long2) AS ?museum_long)

         BIND(COALESCE(?sommario1,?sommario2) AS ?sommario)
         BIND(COALESCE(?sommario_museum1,?sommario_museum2) AS ?sommario_museum)
    }GROUP BY ?arte ?name ?cityUri ?artewiki ?sommario ?image ?museum ?museumwiki ?sommario_museum
"""

sparql_service_url = "http://dbpedia.org/sparql"
result_table = query_wikidata(sparql_query, sparql_service_url)

Nomi=list(compress(result_table.columns, [".value" in i for i in result_table.columns]))
simple_table = result_table[Nomi]
simple_table.columns=[re.sub('.value','', x) for x in simple_table.columns]
lat_column=['lat','museum_lat','city_lat']
long_column=['long','museum_long','city_long']
simple_table[lat_column+long_column]=simple_table[lat_column+long_column].astype('float')
simple_table=simple_table.dropna(axis=0,subset=lat_column+long_column,how='all')
#simple_table=simple_table.dropna(axis=0,subset=['city'])
simple_table=simple_table.reset_index()
#simple_table['city']=[(re.sub(" ","_",x) if not pd.isna(x) else x) for x in [(re.sub(r"[^a-zA-Z0-9]+", " ", x) if not pd.isna(x) else x) for x in simple_table['city']]]

#dbpedia="http://dbpedia.org/page/"
dbp=Namespace("http://dbpedia.org/property/")
dbo=Namespace("http://dbpedia.org/ontology/")
ggart=Namespace("https://ggart.com/ontology/")

arte_museum = ggart['arte_museum']
arte_not_in_museum = ggart['arte_not_in_museum']

g = Graph()

g.namespace_manager.bind('foaf', Namespace('http://xmlns.com/foaf/0.1/'),replace=True)
g.namespace_manager.bind('dbp', Namespace('http://dbpedia.org/property/'),replace=True)
g.namespace_manager.bind('dbo', Namespace('http://dbpedia.org/ontology/'),replace=True)
g.namespace_manager.bind('xsd', Namespace('http://www.w3.org/2001/XMLSchema#'),replace=True)
g.namespace_manager.bind('ggart', ggart,replace=True)

g.add((arte_museum, RDF.type, RDFS.Class))
g.add((arte_museum, RDFS.subClassOf, dbo['Artwork']))

g.add((arte_not_in_museum, RDF.type, RDFS.Class))
g.add((arte_not_in_museum, RDFS.subClassOf, dbo['Artwork']))

for index, row in simple_table.iterrows():
    g.add((URIRef(row['arte']),FOAF.name,Literal(row['name'])))
    #aggiungo wikipedia 
    if not row.isna()['artewiki']:
        g.add((URIRef(row['arte']),FOAF.isPrimaryTopicOf,Literal(row['artewiki'])))

    #aggiungo proprietà city
    if not row.isna()['cityUri']:
        g.add((URIRef(row['arte']),dbp['city'],URIRef(row['cityUri'])))
        if not pd.isna(row['city']):
            g.add((URIRef(row['cityUri']),RDFS.label,Literal(row['city'])))
        if not all(pd.isna(row[['city_lat','city_long']])):
            g.add((URIRef(row['cityUri']),dbp['latitude'],Literal(row['city_lat'],datatype=XSD.float)))
            g.add((URIRef(row['cityUri']),dbp['longitude'],Literal(row['city_long'],datatype=XSD.float)))
#    else:
#        g.add((URIRef(row['arte']),dbp['city'],URIRef(dbpedia+row['city'])))
#        if not pd.isna(row['city']):
#            g.add((URIRef(dbpedia+row['city']),RDFS.label,Literal(row['city'])))
#        if not all(pd.isna(row[['city_lat','city_long']])):
#            g.add((URIRef(dbpedia+row['city']),dbp['latitude'],Literal(row['city_lat'],datatype=XSD.float)))
#            g.add((URIRef(dbpedia+row['city']),dbp['longitude'],Literal(row['city_long'],datatype=XSD.float)))
    #aggiungo arte in museo 
    if not row.isna()['museum']:
        g.add((URIRef(row['arte']),RDF.type,arte_museum))
        #aggiungo museo
        g.add((URIRef(row['arte']),dbo['museum'],URIRef(row['museum'])))
        if not pd.isna(row['museumlabel']):
            g.add((URIRef(row['museum']),RDFS.label,Literal(row['museumlabel'])))
        if not pd.isna(row['sommario_museum']):
            g.add((URIRef(row['museum']),dbo['abstract'],Literal(row['sommario_museum'])))
        #latitudine
        if not all(pd.isna(row[['museum_lat','museum_long']])):
            g.add((URIRef(row['arte']),dbp['latitude'],Literal(row['museum_lat'],datatype=XSD.float)))
            g.add((URIRef(row['arte']),dbp['longitude'],Literal(row['museum_long'],datatype=XSD.float)))
        #wiki
        if not pd.isna(row['museumwiki']):
            g.add((URIRef(row['museum']),FOAF.isPrimaryTopicOf,Literal(row['museumwiki'])))
    else:#non museo class con loc
        g.add((URIRef(row['arte']),RDF.type,arte_not_in_museum))
        if not all(pd.isna(row[['lat','long']])):
            g.add((URIRef(row['arte']),dbp['latitude'],Literal(row['lat'],datatype=XSD.float)))
            g.add((URIRef(row['arte']),dbp['longitude'],Literal(row['long'],datatype=XSD.float)))
    #sommario ed immagine
    if not pd.isna(row['sommario']):
        g.add((URIRef(row['arte']),dbo['abstract'],Literal(row['sommario'])))
    if not pd.isna(row['image']):
        g.add((URIRef(row['arte']),FOAF.depiction,Literal(row['image'])))

g.serialize(destination='graph_dbpedia.ttl', format='turtle')
