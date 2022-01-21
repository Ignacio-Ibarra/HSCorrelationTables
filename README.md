# Tablas de Conversión del Sistema Harmonizado de la Organización Mundial de Aduanas 	

El Sistema Armonizado (HS, *Harmmonized Systems* en inglés) es un sistema internacional de codificación a seis dígitos de bienes intercambiados en el comercio mundial, creado por la 
[*World Custom Organization*](http://www.wcoomd.org/en.aspx) (WCO) en 1988 y actualizado regularmente desde entonces. 

A través de los años nuevos productos aparecen y viejos productos desaparecen del comercio mundial. Asimismo algunos productos se convierten en varios productos o se diferencian en calidad o cambian sus procesos técnicos. Dichos cambios se registran, mediante las versiones del HS. La versión actual es la de 2017, aunque pronto se pondrá en funcionamiento la versión 2022. 

Por ejemplo, si se requiere conocer las exportaciones de la posición 0106.41 ("abejas") sólo se podría obtener una serie temporal a partir del 01.01.2012, debido a que dicha posición se creó a partir de la versión **HS 2012**. 


<img src="https://github.com/Ignacio-Ibarra/HSConversionTables/blob/main/img/010641.html" />

Fuente: [UN HSTracker](https://hstracker.wto.org/#).

La obtención de una serie más larga sólo se podría conseguir sacrificando precisión. Ejemplo, el código 0106.90, disponible tanto en la versión **HS 2007**, como **HS 2002** es un código que fue transformado en la versión **HS 2012** y **HS 2017** en las posiciones **0106.41**, 0106.49 y 0106.90. Por ende para obtener una serie desde el 01.01.2002 en adelante, es necesario requerir que las exportaciones entre 2002 y 2011 sean para el producto 0106.90 y desde 2012 en adelante sean para la suma agregada de las exportaciones de los productos 0106.41 ("insectos --abejas"), 0106.49 ("insectos --los demás") y 0106.90 ("los demás animales vivos --los demás", lo que incluye a la rana toro o rana catesbeiana, larvas, postmetamórficos, juveniles y adultos). Es decir, ya no serían las exportaciones de "abejas" desde 2012 en adelante sino que serían las exportaciones agregadas de los "demás animales vivos (excl. mamíferos, reptiles y aves no presentes en los capítulos 01.01 al 01.05)". 

Inclusive, si fuera necesaria una serie de tiempo más larga debería requerirse una cantidad mucho mayor de posiciones para poder tener una serie más homogénea, tal como se observa en la siguiente imagen. 

<img src="https://github.com/Ignacio-Ibarra/HSConversionTables/blob/main/img/010600.svg" />

Fuente: [UN HSTracker](https://hstracker.wto.org/#)

Tal como se observa en la imagen para poder obtener una serie desde 1992 es necesario requerir una gran cantidad de posiciones y realizar una agregación, lo que implica perder precisión en la definición. En este caso el producto quedaría definido como "animales vivos (excl. caballos, aznos, mulas, burdéganos, animales bovinos, cerdos, ovejas, cabras, aves de corral, peces, crustáceos, moluscos y otros invertebrados acuáticos y cultivos de microorganismos)". 

El objetivo del presente trabajo es diseñar una herramienta que permita saber de antemano cuál es el la ventana temporal disponible de cierto producto o cuál es la pérdida de precisión en la definición de un producto para ampliar el espacio temporal. 
