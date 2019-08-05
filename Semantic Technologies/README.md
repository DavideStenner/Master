# Semantic Technologies

## Creazione del Grafo

```
q=query_maker()
q.updatedb()
```

## Trovare Opera d'arte più vicina

Prima creo i riferimenti geospaziali delle opere d'arte con art_geomapping poi ricerco l'opera d'arte più vicina
```
q.art_geomapping(lat=45.465454,long=9.186516)
q.nearest(table=q.artmap,lat=45.465454,long=9.186516)
```

Per trovare le opere d'arte in un certo raggio dalla propria posizione:
```
q.radius(table=q.artmap,lat=45.465454,long=9.186516,radius=100)

```
## Opera d'arte per Nome
```
q.string_finder(name='The Starry Night')
q.artfind
```
## Musei
```
q.collect_museum()
q.museum
```
## Opere d'arte non nei musei
```
q.collect_not_in_museum()
q.not_in_museum
```
Opere all'interno di musei specifici
```
q.art_in_museum_finder('Museo de Antioquia')
q.artfind
```
