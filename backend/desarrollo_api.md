esto es lo que quiero si es que aun no contempla el sistema, no me da tiempo de leer todo el codigo pero... 
se necesita manejar
Registro, edicion eliminacion de empresas, y edicion en empresas_sire, si empresas se elimina, empresas sire tambien. 

cuando se genere las propeustas, poder hacerlo  por periodo, aqui no me voy a complicar, pero si que se pueda por una sola empresa, eso si lo hace, pero que tambien por un grupo de empresas determinadas, una List.  que serían una lista de rucs. eso para crear y guardar el csv, pero que tambien lo devuelva en xlsx para el usuario. Aqui que no permita editar, si se ha hecho modifiaciones desde SOL. entonces que descargue primero. Ahora esta como idenpotente para evitar la duplicacion y en su lugar solo se actualice.


luego en los descargar los xml por empresas en un periodo dado, y que no tenga limite. 
Que se pueda descargar los xml de una empresa, de un grupo de empresas. e igual que los devuelva. 
Y aqui en proxima instancia veremos que cuando se consulte el xml, lo que se espera es el comprobante pero con todos sus detalles. 
Y cuando se consulte el reporte mensual de compras, traiga todos los comprobantes con sus detalles y especificando al usuario que tnantos comprobantes que marcaron ERROR o NOT_FOUND deben ser revizados manualmente. 


# nuevas instrucciones
Empecemos por lo primero. Pero eso es lo que se espera de esta api con fastapi. 
aunque mira, no lo esta creando en erp_sunat/data sino en erp_sunat/backend/data 
Pero bueno, ya despues vemos eso, no me interesa por ahora mientras funcione. 

Lo que quiero ahora es, un endpoint que permita la recoleccion del detalle. sería tabla de comprobantes de ese periodo, pero con los datos del detalle y precio o algo asi. Algo bonito que se pueda ver de un chamapso porque algunas traen mas de un producto y su precio y eso, para altoque saber que es deducible o no, eso ya lo hace el contador., pero nuestra labor es mostrarle lo mejor de lo mejor. 
Los datos que guarda la bd del xml es esto. 

