"""
Diccionario de códigos del Censo 2018 Colombia - Tabla Individual
Fuente: DANE - Documentación Censo Nacional de Población y Vivienda 2018

Este archivo centraliza los catálogos oficiales para validación de datos censales.
"""

# Sexo (P_SEXO)
SEXO = {
    1: "Hombre",
    2: "Mujer"
}

# Pertenencia étnica (PA1_GRP_ETNIC)
GRUPO_ETNICO = {
    1: "Indígena",
    2: "Raizal de San Andrés y Providencia",
    3: "Palenquero de San Basilio",
    4: "Negro(a), Mulato(a), Afrocolombiano(a)",
    5: "Ninguno de los anteriores",  # No étnico
    6: "Indígena",  # Puede haber duplicación en codificación
    9: "Ignorado"
}

# Estado civil (P_EST_CIVIL) - para mayores de 12 años
ESTADO_CIVIL = {
    1: "Soltero(a)",
    2: "Casado(a)",
    3: "Unido(a)",
    4: "Separado(a)",
    5: "Divorciado(a)",
    6: "Viudo(a)",
    7: "Soltero(a) - menor 12 años",
    9: "Ignorado"
}

# Trabajó la semana pasada (P_TRABAJO) - para mayores de 5 años
TRABAJO = {
    0: "Menor de 5 años (no pregunta)",
    1: "Sí trabajó",
    2: "No trabajó, tenía empleo",
    3: "No trabajó, buscó empleo",
    4: "No trabajó, quehaceres del hogar",
    5: "No trabajó, estudiaba",
    6: "No trabajó, jubilado/pensionado",
    7: "No trabajó, otra razón",
    8: "No trabajó, sin especificar",
    9: "Ignorado"
}

# Sabe leer y escribir (P_ALFABETA) - para mayores de 5 años
ALFABETA = {
    1: "Sí sabe",
    2: "No sabe",
    9: "Ignorado"
}

# Asistencia educativa (PA_ASISTENCIA) - para mayores de 5 años
ASISTENCIA = {
    1: "Sí asiste",
    2: "No asiste",
    9: "Ignorado"
}

# Enfermedad crónica (P_ENFERMO)
ENFERMO = {
    1: "Sí tiene",
    2: "No tiene",
    9: "Ignorado"
}

# Nivel educativo (P_NIVEL_ANOSR) - años aprobados
NIVEL_EDUCATIVO_ANOS = {
    0: "Ninguno",
    1: "Primero",
    2: "Segundo",
    3: "Tercero",
    4: "Cuarto",
    5: "Quinto",
    6: "Sexto",
    7: "Séptimo",
    8: "Octavo",
    9: "Noveno",
    10: "Décimo",
    11: "Once",
    99: "Ignorado"
}

# Tipo de registro (TIPO_REG)
TIPO_REG = {
    1: "Vivienda",
    2: "Hogar",
    5: "Persona"
}

# Departamentos de Colombia (U_DPTO) - códigos DIVIPOLA reales del DANE
DEPARTAMENTOS_DANE = {
    5:  "Antioquia",
    8:  "Atlántico",
    11: "Bogotá D.C.",
    13: "Bolívar",
    15: "Boyacá",
    17: "Caldas",
    18: "Caquetá",
    19: "Cauca",
    20: "Cesar",
    23: "Córdoba",
    25: "Cundinamarca",
    27: "Chocó",
    41: "Huila",
    44: "La Guajira",
    47: "Magdalena",
    50: "Meta",
    52: "Nariño",
    54: "Norte de Santander",
    63: "Quindío",
    66: "Risaralda",
    68: "Santander",
    70: "Sucre",
    73: "Tolima",
    76: "Valle del Cauca",
    81: "Arauca",
    85: "Casanare",
    86: "Putumayo",
    88: "San Andrés y Providencia",
    91: "Amazonas",
    94: "Guainía",
    95: "Guaviare",
    97: "Vaupés",
    99: "Vichada",
}

# Municipios de Colombia (U_DPTO, U_MPIO) - catálogo DIVIPOLA DANE
# Clave: (codigo_dpto, codigo_mpio)
MUNICIPIOS_DANE = {
    # Amazonas (91)
    (91, 1): "Leticia", (91, 263): "El Encanto", (91, 405): "La Chorrera",
    (91, 407): "La Pedrera", (91, 430): "La Victoria", (91, 460): "Mirití-Paraná",
    (91, 530): "Puerto Alegría", (91, 536): "Puerto Arica", (91, 540): "Puerto Nariño",
    (91, 669): "Puerto Santander", (91, 798): "Tarapacá",
    # Antioquia (05)
    (5, 1): "Medellín", (5, 45): "Apartadó", (5, 88): "Caucasia",
    (5, 147): "Chigorodó", (5, 250): "Envigado", (5, 266): "Fredonia",
    (5, 282): "Girardota", (5, 308): "Itagüí", (5, 368): "La Estrella",
    (5, 376): "La Unión", (5, 380): "Barbosa", (5, 440): "Marinilla",
    (5, 467): "Montebello", (5, 591): "Rionegro", (5, 615): "Sabaneta",
    (5, 658): "San Pedro de los Milagros", (5, 756): "Turbo", (5, 790): "Yarumal",
    # Arauca (81)
    (81, 1): "Arauca", (81, 65): "Arauquita", (81, 220): "Cravo Norte",
    (81, 300): "Fortul", (81, 591): "Puerto Rondón", (81, 736): "Saravena",
    (81, 794): "Tame",
    # Atlántico (08)
    (8, 1): "Barranquilla", (8, 137): "Galapa", (8, 296): "Juan de Acosta",
    (8, 372): "Luruaco", (8, 421): "Malambo", (8, 433): "Manatí",
    (8, 520): "Palmar de Varela", (8, 549): "Piojó", (8, 573): "Polonuevo",
    (8, 634): "Sabanagrande", (8, 638): "Sabanalarga", (8, 675): "Santa Lucía",
    (8, 770): "Soledad", (8, 832): "Tubará", (8, 849): "Usiacurí",
    # Bogotá D.C. (11)
    (11, 1): "Bogotá D.C.",
    # Bolívar (13)
    (13, 1): "Cartagena", (13, 6): "Achí", (13, 30): "Altos del Rosario",
    (13, 52): "Arenal", (13, 62): "Arjona", (13, 74): "Arroyohondo",
    (13, 140): "Calamar", (13, 160): "Cantagallo", (13, 188): "Cicuco",
    (13, 212): "Córdoba", (13, 222): "Clemencia", (13, 244): "El Carmen de Bolívar",
    (13, 248): "El Guamo", (13, 268): "El Peñón", (13, 300): "Hatillo de Loba",
    (13, 430): "Magangué", (13, 433): "Mahates", (13, 440): "Margarita",
    (13, 442): "María la Baja", (13, 458): "Montecristo", (13, 468): "Mompós",
    (13, 473): "Morales", (13, 549): "Norosí", (13, 580): "Pinillos",
    (13, 600): "Regidor", (13, 620): "Río Viejo", (13, 647): "San Cristóbal",
    (13, 650): "San Estanislao", (13, 654): "San Fernando", (13, 655): "San Jacinto",
    (13, 657): "San Jacinto del Cauca", (13, 667): "San Juan Nepomuceno",
    (13, 670): "San Martín de Loba", (13, 673): "San Pablo", (13, 683): "Santa Catalina",
    (13, 688): "Santa Rosa", (13, 744): "Simití", (13, 760): "Soplaviento",
    (13, 780): "Talaigua Nuevo", (13, 810): "Tiquisio", (13, 836): "Turbaco",
    (13, 838): "Turbaná", (13, 873): "Villanueva", (13, 894): "Zambrano",
    # Boyacá (15)
    (15, 1): "Tunja", (15, 22): "Almeida", (15, 47): "Aquitania",
    (15, 51): "Arcabuco", (15, 87): "Belén", (15, 90): "Berbeo",
    (15, 92): "Betéitiva", (15, 97): "Boavita", (15, 104): "Boyacá",
    (15, 109): "Briceño", (15, 114): "Buenavista", (15, 131): "Campohermoso",
    (15, 162): "Cerinza", (15, 172): "Chinavita", (15, 176): "Chiquinquirá",
    (15, 180): "Chiscas", (15, 183): "Chita", (15, 185): "Chitaraque",
    (15, 187): "Chivatá", (15, 189): "Ciénega", (15, 204): "Cómbita",
    (15, 212): "Coper", (15, 215): "Corrales", (15, 218): "Covarachía",
    (15, 224): "Cubará", (15, 226): "Cucaita", (15, 232): "Cuítiva",
    (15, 236): "Duitama", (15, 238): "El Cocuy", (15, 244): "El Espino",
    (15, 248): "Firavitoba", (15, 272): "Floresta", (15, 276): "Gachantivá",
    (15, 293): "Gameza", (15, 296): "Garagoa", (15, 299): "Guacamayas",
    (15, 317): "Guateque", (15, 322): "Guayatá", (15, 325): "Güicán de la Sierra",
    (15, 332): "Iza", (15, 362): "Jenesano", (15, 367): "Jericó",
    (15, 380): "Labranzagrande", (15, 401): "La Capilla", (15, 403): "La Uvita",
    (15, 407): "Villa de Leyva", (15, 425): "Macanal", (15, 442): "Maripí",
    (15, 455): "Miraflores", (15, 464): "Mongua", (15, 466): "Monguí",
    (15, 469): "Moniquirá", (15, 476): "Motavita", (15, 480): "Muzo",
    (15, 491): "Nobsa", (15, 494): "Nuevo Colón", (15, 500): "Oicatá",
    (15, 507): "Otanche", (15, 511): "Pachavita", (15, 514): "Páez",
    (15, 516): "Paipa", (15, 518): "Pajarito", (15, 522): "Panqueba",
    (15, 531): "Pauna", (15, 533): "Paya", (15, 537): "Paz de Río",
    (15, 542): "Pesca", (15, 550): "Pisba", (15, 572): "Puerto Boyacá",
    (15, 580): "Quípama", (15, 599): "Ramiriquí", (15, 600): "Ráquira",
    (15, 621): "Rondón", (15, 632): "Saboyá", (15, 638): "Sáchica",
    (15, 646): "Samacá", (15, 660): "San Eduardo", (15, 664): "San José de Pare",
    (15, 667): "San Luis de Gaceno", (15, 673): "San Mateo",
    (15, 676): "San Miguel de Sema", (15, 681): "San Pablo de Borbur",
    (15, 686): "Santana", (15, 690): "Santa María", (15, 693): "Santa Rosa de Viterbo",
    (15, 696): "Santa Sofía", (15, 720): "Sativasur", (15, 723): "Sativanorte",
    (15, 740): "Siachoque", (15, 753): "Soatá", (15, 755): "Socotá",
    (15, 757): "Socha", (15, 759): "Sogamoso", (15, 761): "Somondoco",
    (15, 762): "Sora", (15, 763): "Sotaquirá", (15, 764): "Soracá",
    (15, 774): "Susacón", (15, 776): "Sutamarchán", (15, 778): "Sutatenza",
    (15, 790): "Tasco", (15, 798): "Tenza", (15, 804): "Tibaná",
    (15, 806): "Tibasosa", (15, 808): "Tinjacá", (15, 810): "Tipacoque",
    (15, 814): "Toca", (15, 816): "Togüí", (15, 820): "Tópaga",
    (15, 822): "Tota", (15, 832): "Tununguá", (15, 835): "Turmequé",
    (15, 837): "Tuta", (15, 839): "Tutazá", (15, 842): "Úmbita",
    (15, 861): "Ventaquemada", (15, 879): "Viracachá", (15, 897): "Zetaquira",
    # Caldas (17)
    (17, 1): "Manizales", (17, 13): "Aguadas", (17, 42): "Anserma",
    (17, 50): "Aranzazu", (17, 88): "Belalcázar", (17, 174): "Chinchiná",
    (17, 272): "Filadelfia", (17, 380): "La Dorada", (17, 388): "La Merced",
    (17, 433): "Manzanares", (17, 442): "Marmato", (17, 444): "Marquetalia",
    (17, 446): "Marulanda", (17, 486): "Neira", (17, 495): "Norcasia",
    (17, 513): "Pácora", (17, 524): "Palestina", (17, 541): "Pensilvania",
    (17, 614): "Riosucio", (17, 616): "Risaralda", (17, 653): "Salamina",
    (17, 662): "Samaná", (17, 665): "San José", (17, 777): "Supía",
    (17, 867): "Victoria", (17, 873): "Villamaría", (17, 877): "Viterbo",
    # Caquetá (18)
    (18, 1): "Florencia", (18, 29): "Albania", (18, 94): "Belén de los Andaquíes",
    (18, 150): "Cartagena del Chairá", (18, 205): "Curillo", (18, 247): "El Doncello",
    (18, 256): "El Paujil", (18, 410): "La Montañita", (18, 460): "Milán",
    (18, 479): "Morelia", (18, 592): "Puerto Rico", (18, 610): "San José del Fragua",
    (18, 753): "San Vicente del Caguán", (18, 756): "Solano",
    (18, 785): "Solita", (18, 860): "Valparaíso",
    # Casanare (85)
    (85, 1): "Yopal", (85, 10): "Aguazul", (85, 15): "Chameza",
    (85, 125): "Hato Corozal", (85, 136): "La Salina", (85, 139): "Maní",
    (85, 162): "Monterrey", (85, 225): "Nunchía", (85, 230): "Orocué",
    (85, 250): "Paz de Ariporo", (85, 263): "Pore", (85, 279): "Recetor",
    (85, 300): "Sabanalarga", (85, 315): "Sácama", (85, 325): "San Luis de Palenque",
    (85, 400): "Támara", (85, 410): "Tauramena", (85, 430): "Trinidad",
    (85, 440): "Villanueva",
    # Cauca (19)
    (19, 1): "Popayán", (19, 22): "Almaguer", (19, 50): "Argelia",
    (19, 75): "Balboa", (19, 100): "Bolívar", (19, 110): "Buenos Aires",
    (19, 130): "Cajibío", (19, 137): "Caldono", (19, 142): "Caloto",
    (19, 212): "Corinto", (19, 256): "El Tambo", (19, 290): "Florencia",
    (19, 300): "Guachené", (19, 318): "Guapí", (19, 355): "Inzá",
    (19, 364): "Jambaló", (19, 392): "La Sierra", (19, 397): "La Vega",
    (19, 418): "López de Micay", (19, 450): "Mercaderes", (19, 455): "Miranda",
    (19, 473): "Morales", (19, 513): "Padilla", (19, 517): "Páez",
    (19, 532): "Patía", (19, 533): "Piamonte", (19, 548): "Piendamó-Tunía",
    (19, 573): "Puerto Tejada", (19, 585): "Puracé", (19, 622): "Rosas",
    (19, 693): "San Sebastián", (19, 698): "Santander de Quilichao",
    (19, 701): "Santa Rosa", (19, 743): "Silvia", (19, 760): "Sotara",
    (19, 780): "Suárez", (19, 785): "Sucre", (19, 807): "Timbío",
    (19, 809): "Timbiquí", (19, 821): "Toribío", (19, 824): "Totoró",
    (19, 845): "Villa Rica",
    # Cesar (20)
    (20, 1): "Valledupar", (20, 11): "Aguachica", (20, 13): "Agustín Codazzi",
    (20, 32): "Astrea", (20, 45): "Becerril", (20, 60): "Bosconia",
    (20, 175): "Chimichagua", (20, 178): "Chiriguaná", (20, 228): "Curumaní",
    (20, 238): "El Copey", (20, 250): "El Paso", (20, 295): "Gamarra",
    (20, 310): "González", (20, 383): "La Gloria", (20, 400): "La Jagua de Ibirico",
    (20, 443): "Manaure Balcón del Cesar", (20, 517): "Pailitas",
    (20, 550): "Pelaya", (20, 570): "Pueblo Bello", (20, 614): "Río de Oro",
    (20, 621): "La Paz", (20, 710): "San Alberto", (20, 750): "San Diego",
    (20, 770): "San Martín", (20, 787): "Tamalameque",
    # Chocó (27)
    (27, 1): "Quibdó", (27, 6): "Acandí", (27, 25): "Alto Baudó",
    (27, 50): "Atrato", (27, 73): "Bagadó", (27, 75): "Bahía Solano",
    (27, 77): "Bajo Baudó", (27, 99): "Bojayá", (27, 135): "El Cantón del San Pablo",
    (27, 150): "Carmen del Darién", (27, 160): "Cértegui", (27, 205): "Condoto",
    (27, 245): "El Carmen de Atrato", (27, 250): "El Litoral del San Juan",
    (27, 361): "Istmina", (27, 372): "Juradó", (27, 413): "Lloró",
    (27, 425): "Medio Atrato", (27, 430): "Medio Baudó", (27, 450): "Medio San Juan",
    (27, 491): "Nóvita", (27, 495): "Nuquí", (27, 580): "Río Iró",
    (27, 600): "Río Quito", (27, 615): "Riosucio", (27, 660): "San José del Palmar",
    (27, 745): "Sipí", (27, 787): "Tadó", (27, 800): "Unguía",
    (27, 810): "Unión Panamericana",
    # Córdoba (23)
    (23, 1): "Montería", (23, 68): "Ayapel", (23, 79): "Buenavista",
    (23, 90): "Canalete", (23, 162): "Cereté", (23, 168): "Chimá",
    (23, 182): "Chinú", (23, 189): "Ciénaga de Oro", (23, 300): "Cotorra",
    (23, 350): "La Apartada", (23, 417): "Lorica", (23, 419): "Los Córdobas",
    (23, 464): "Momil", (23, 466): "Montelíbano", (23, 500): "Moñitos",
    (23, 555): "Planeta Rica", (23, 570): "Pueblo Nuevo", (23, 574): "Puerto Escondido",
    (23, 580): "Puerto Libertador", (23, 586): "Purísima de la Concepción",
    (23, 660): "Sahagún", (23, 670): "San Andrés de Sotavento",
    (23, 672): "San Antero", (23, 675): "San Bernardo del Viento",
    (23, 678): "San Carlos", (23, 682): "San José de Uré", (23, 686): "San Pelayo",
    (23, 807): "Tierralta", (23, 815): "Tuchín", (23, 855): "Valencia",
    # Cundinamarca (25)
    (25, 1): "Agua de Dios", (25, 19): "Albán", (25, 35): "Anapoima",
    (25, 40): "Anolaima", (25, 53): "Arbeláez", (25, 86): "Beltrán",
    (25, 95): "Bituima", (25, 99): "Bojacá", (25, 120): "Cabrera",
    (25, 123): "Cachipay", (25, 126): "Cajicá", (25, 148): "Caparrapí",
    (25, 151): "Cáqueza", (25, 154): "Carmen de Carupa", (25, 168): "Chaguaní",
    (25, 175): "Chía", (25, 178): "Chipaque", (25, 181): "Choachí",
    (25, 183): "Chocontá", (25, 200): "Cogua", (25, 214): "Cota",
    (25, 224): "Cucunubá", (25, 245): "El Colegio", (25, 258): "El Peñón",
    (25, 260): "El Rosal", (25, 269): "Facatativá", (25, 279): "Fomeque",
    (25, 281): "Fosca", (25, 286): "Funza", (25, 288): "Fúquene",
    (25, 290): "Fusagasugá", (25, 293): "Gachalá", (25, 295): "Gachancipá",
    (25, 297): "Gachetá", (25, 299): "Gama", (25, 307): "Girardot",
    (25, 312): "Granada", (25, 317): "Guachetá", (25, 320): "Guaduas",
    (25, 322): "Guasca", (25, 324): "Guataquí", (25, 326): "Guatavita",
    (25, 328): "Guayabal de Síquima", (25, 335): "Guayabetal",
    (25, 339): "Gutiérrez", (25, 368): "Jerusalén", (25, 372): "Junín",
    (25, 377): "La Calera", (25, 386): "La Mesa", (25, 394): "La Palma",
    (25, 398): "La Peña", (25, 402): "La Vega", (25, 407): "Lenguazaque",
    (25, 426): "Macheta", (25, 430): "Madrid", (25, 436): "Manta",
    (25, 438): "Medina", (25, 473): "Mosquera", (25, 483): "Nariño",
    (25, 486): "Nemocón", (25, 488): "Nilo", (25, 489): "Nimaima",
    (25, 491): "Nocaima", (25, 506): "Venecia", (25, 513): "Pacho",
    (25, 518): "Paime", (25, 524): "Pandi", (25, 530): "Paratebueno",
    (25, 535): "Pasca", (25, 572): "Puerto Salgar", (25, 580): "Pulí",
    (25, 592): "Quebradanegra", (25, 594): "Quetame", (25, 596): "Quipile",
    (25, 599): "Apulo", (25, 612): "Ricaurte", (25, 645): "San Antonio del Tequendama",
    (25, 649): "San Bernardo", (25, 653): "San Cayetano", (25, 658): "San Francisco",
    (25, 662): "San Juan de Río Seco", (25, 718): "Sasaima", (25, 736): "Sesquilé",
    (25, 740): "Sibaté", (25, 743): "Silvania", (25, 745): "Simijaca",
    (25, 754): "Soacha", (25, 758): "Sopó", (25, 769): "Subachoque",
    (25, 772): "Suesca", (25, 777): "Supatá", (25, 779): "Susa",
    (25, 781): "Sutatausa", (25, 785): "Tabio", (25, 793): "Tausa",
    (25, 797): "Tena", (25, 799): "Tenjo", (25, 805): "Tibacuy",
    (25, 807): "Tibirita", (25, 815): "Tocaima", (25, 817): "Tocancipá",
    (25, 823): "Topaipí", (25, 839): "Ubalá", (25, 841): "Ubaque",
    (25, 843): "Villa de San Diego de Ubaté", (25, 845): "Une",
    (25, 851): "Útica", (25, 862): "Vergara", (25, 867): "Vianí",
    (25, 871): "Villagómez", (25, 873): "Villapinzón", (25, 875): "Villeta",
    (25, 878): "Viotá", (25, 885): "Yacopí", (25, 898): "Zipacón",
    (25, 899): "Zipaquirá",
    # Guainía (94)
    (94, 1): "Inírida", (94, 343): "Barranco Minas", (94, 663): "Mapiripana",
    (94, 883): "San Felipe", (94, 884): "Puerto Colombia", (94, 885): "La Guadalupe",
    (94, 886): "Cacahual", (94, 887): "Pana Pana", (94, 888): "Morichal",
    # Guaviare (95)
    (95, 1): "San José del Guaviare", (95, 15): "Calamar",
    (95, 25): "El Retorno", (95, 200): "Miraflores",
    # Huila (41)
    (41, 1): "Neiva", (41, 6): "Acevedo", (41, 13): "Agrado",
    (41, 16): "Aipe", (41, 20): "Algeciras", (41, 26): "Altamira",
    (41, 78): "Baraya", (41, 132): "Campoalegre", (41, 206): "Colombia",
    (41, 244): "Elías", (41, 298): "Garzón", (41, 306): "Gigante",
    (41, 319): "Guadalupe", (41, 349): "Hobo", (41, 357): "Iquira",
    (41, 359): "Isnos", (41, 378): "La Argentina", (41, 396): "La Plata",
    (41, 483): "Nátaga", (41, 503): "Oporapa", (41, 518): "Paicol",
    (41, 524): "Palermo", (41, 530): "Palestina", (41, 548): "Pital",
    (41, 551): "Pitalito", (41, 615): "Rivera", (41, 660): "Saladoblanco",
    (41, 668): "San Agustín", (41, 676): "Santa María", (41, 770): "Suaza",
    (41, 791): "Tarqui", (41, 797): "Tesalia", (41, 799): "Tello",
    (41, 801): "Teruel", (41, 807): "Timaná", (41, 872): "Villavieja",
    (41, 885): "Yaguará",
    # La Guajira (44)
    (44, 1): "Riohacha", (44, 35): "Albania", (44, 78): "Barrancas",
    (44, 90): "Dibulla", (44, 98): "Distracción", (44, 110): "El Molino",
    (44, 143): "Fonseca", (44, 217): "Hatonuevo", (44, 279): "La Jagua del Pilar",
    (44, 378): "Maicao", (44, 420): "Manaure", (44, 430): "Mohan",
    (44, 560): "Páez", (44, 650): "San Juan del Cesar",
    (44, 847): "Uribia", (44, 855): "Urumita", (44, 874): "Villanueva",
    # Magdalena (47)
    (47, 1): "Santa Marta", (47, 30): "Algarrobo", (47, 53): "Aracataca",
    (47, 58): "Ariguaní", (47, 161): "Cerro de San Antonio", (47, 170): "Chivolo",
    (47, 189): "Ciénaga", (47, 205): "Concordia", (47, 245): "El Banco",
    (47, 258): "El Piñón", (47, 268): "El Retén", (47, 288): "Fundación",
    (47, 318): "Guamal", (47, 460): "Nueva Granada", (47, 541): "Pedraza",
    (47, 545): "Pijiño del Carmen", (47, 551): "Pivijay", (47, 555): "Plato",
    (47, 570): "Pueblo Viejo", (47, 605): "Remolino", (47, 660): "Sabanas de San Ángel",
    (47, 675): "Salamina", (47, 703): "San Sebastián de Buenavista",
    (47, 707): "San Zenón", (47, 720): "Santa Ana", (47, 745): "Santa Bárbara de Pinto",
    (47, 798): "Sitionuevo", (47, 960): "Tenerife", (47, 980): "Zapayán",
    # Meta (50)
    (50, 1): "Villavicencio", (50, 6): "Acacías", (50, 110): "Barranca de Upía",
    (50, 124): "Cabuyaro", (50, 150): "Castilla la Nueva", (50, 223): "Cubarral",
    (50, 226): "Cumaral", (50, 245): "El Calvario", (50, 251): "El Castillo",
    (50, 270): "El Dorado", (50, 287): "Fuente de Oro", (50, 313): "Granada",
    (50, 318): "Guamal", (50, 325): "Mapiripán", (50, 330): "Mesetas",
    (50, 350): "La Macarena", (50, 400): "Uribe", (50, 450): "Lejanías",
    (50, 568): "Puerto Concordia", (50, 573): "Puerto Gaitán", (50, 577): "Puerto Lleras",
    (50, 590): "Puerto López", (50, 606): "Puerto Rico", (50, 680): "Restrepo",
    (50, 683): "San Carlos de Guaroa", (50, 686): "San Juan de Arama",
    (50, 689): "San Juanito", (50, 711): "San Martín", (50, 790): "Vistahermosa",
    # Nariño (52)
    (52, 1): "Pasto", (52, 19): "Albán", (52, 22): "Aldana",
    (52, 36): "Ancuyá", (52, 51): "Arboleda", (52, 79): "Barbacoas",
    (52, 83): "Belén", (52, 110): "Buesaco", (52, 203): "Colón",
    (52, 207): "Consacá", (52, 210): "Contadero", (52, 215): "Córdoba",
    (52, 224): "Cuaspud Carlosama", (52, 227): "Cumbal", (52, 233): "Cumbitara",
    (52, 240): "Chachagüí", (52, 250): "El Charco", (52, 254): "El Peñol",
    (52, 256): "El Rosario", (52, 258): "El Tablón de Gómez", (52, 260): "El Tambo",
    (52, 287): "Funes", (52, 317): "Guachucal", (52, 320): "Guaitarilla",
    (52, 323): "Gualmatán", (52, 352): "Iles", (52, 354): "Imués",
    (52, 356): "Ipiales", (52, 378): "La Cruz", (52, 381): "La Florida",
    (52, 385): "La Llanada", (52, 390): "La Tola", (52, 399): "La Unión",
    (52, 405): "Leiva", (52, 411): "Linares", (52, 418): "Los Andes",
    (52, 427): "Magüí", (52, 435): "Mallama", (52, 473): "Mosquera",
    (52, 480): "Nariño", (52, 490): "Olaya Herrera", (52, 506): "Ospina",
    (52, 520): "Francisco Pizarro", (52, 540): "Policarpa", (52, 560): "Potosí",
    (52, 565): "Providencia", (52, 573): "Puerres", (52, 585): "Pupiales",
    (52, 612): "Ricaurte", (52, 621): "Roberto Payán", (52, 678): "Samaniego",
    (52, 683): "Sandoná", (52, 685): "San Bernardo", (52, 687): "San Lorenzo",
    (52, 693): "San Pablo", (52, 694): "San Pedro de Cartago", (52, 696): "Santa Bárbara",
    (52, 699): "Santacruz", (52, 720): "Sapuyes", (52, 786): "Taminango",
    (52, 788): "Tangua", (52, 835): "San Andrés de Tumaco", (52, 838): "Túquerres",
    (52, 885): "Yacuanquer",
    # Norte de Santander (54)
    (54, 1): "Cúcuta", (54, 3): "Ábrego", (54, 51): "Arboledas",
    (54, 99): "Bochalema", (54, 109): "Bucarasica", (54, 125): "Cácota",
    (54, 128): "Cáchira", (54, 172): "Chinácota", (54, 174): "Chitagá",
    (54, 206): "Convención", (54, 223): "Cucutilla", (54, 239): "Durania",
    (54, 245): "El Carmen", (54, 250): "El Tarra", (54, 261): "El Zulia",
    (54, 313): "Gramalote", (54, 344): "Hacarí", (54, 347): "Herrán",
    (54, 377): "Labateca", (54, 385): "La Esperanza", (54, 398): "La Playa de Belén",
    (54, 405): "Los Patios", (54, 418): "Lourdes", (54, 480): "Mutiscua",
    (54, 498): "Ocaña", (54, 518): "Pamplona", (54, 520): "Pamplonita",
    (54, 533): "Puerto Santander", (54, 553): "Ragonvalia",
    (54, 599): "Salazar", (54, 660): "San Calixto", (54, 673): "San Cayetano",
    (54, 680): "Santiago", (54, 720): "Sardinata", (54, 743): "Silos",
    (54, 800): "Teorama", (54, 810): "Tibú", (54, 820): "Toledo",
    (54, 871): "Villa Caro", (54, 874): "Villa del Rosario",
    # Putumayo (86)
    (86, 1): "Mocoa", (86, 219): "Colón", (86, 320): "Orito",
    (86, 568): "Puerto Asís", (86, 569): "Puerto Caicedo", (86, 571): "Puerto Guzmán",
    (86, 573): "Leguízamo", (86, 749): "Sibundoy", (86, 755): "San Francisco",
    (86, 757): "San Miguel", (86, 760): "Santiago", (86, 865): "Valle del Guamuez",
    (86, 885): "Villagarzón",
    # Quindío (63)
    (63, 1): "Armenia", (63, 111): "Buenavista", (63, 130): "Calarcá",
    (63, 190): "Circasia", (63, 212): "Córdoba", (63, 272): "Filandia",
    (63, 302): "Génova", (63, 401): "La Tebaida", (63, 470): "Montenegro",
    (63, 548): "Pijao", (63, 594): "Quimbaya", (63, 690): "Salento",
    # Risaralda (66)
    (66, 1): "Pereira", (66, 45): "Apía", (66, 75): "Balboa",
    (66, 88): "Belén de Umbría", (66, 170): "Dosquebradas", (66, 318): "Guática",
    (66, 383): "La Celia", (66, 400): "La Virginia", (66, 440): "Marsella",
    (66, 456): "Mistrató", (66, 572): "Pueblo Rico", (66, 594): "Quinchía",
    (66, 682): "Santa Rosa de Cabal", (66, 687): "Santuario",
    # San Andrés y Providencia (88)
    (88, 1): "San Andrés", (88, 564): "Providencia",
    # Santander (68)
    (68, 1): "Bucaramanga", (68, 13): "Aguada", (68, 20): "Albania",
    (68, 51): "Aratoca", (68, 77): "Barbosa", (68, 79): "Barichara",
    (68, 81): "Barrancabermeja", (68, 92): "Betulia", (68, 101): "Bolívar",
    (68, 121): "Cabrera", (68, 132): "California", (68, 147): "Capitanejo",
    (68, 152): "Carcasí", (68, 160): "Cepitá", (68, 162): "Cerrito",
    (68, 167): "Charalá", (68, 169): "Charta", (68, 176): "Chima",
    (68, 179): "Chipatá", (68, 190): "Cimitarra", (68, 207): "Concepción",
    (68, 209): "Confines", (68, 211): "Contratación", (68, 217): "Coromoro",
    (68, 229): "Curití", (68, 235): "El Carmen de Chucurí",
    (68, 245): "El Guacamayo", (68, 250): "El Peñón", (68, 255): "El Playón",
    (68, 264): "Encino", (68, 266): "Enciso", (68, 271): "Florián",
    (68, 276): "Floridablanca", (68, 296): "Galán", (68, 298): "Gambita",
    (68, 307): "Girón", (68, 318): "Guaca", (68, 320): "Guadalupe",
    (68, 322): "Guapotá", (68, 324): "Guavatá", (68, 327): "Güepsa",
    (68, 344): "Hato", (68, 368): "Jesús María", (68, 370): "Jordán",
    (68, 377): "La Belleza", (68, 385): "Landázuri", (68, 397): "La Paz",
    (68, 406): "Lebríja", (68, 418): "Los Santos", (68, 425): "Macaravita",
    (68, 432): "Málaga", (68, 444): "Matanza", (68, 464): "Mogotes",
    (68, 468): "Molagavita", (68, 498): "Ocamonte", (68, 500): "Oiba",
    (68, 502): "Onzaga", (68, 522): "Palmar", (68, 524): "Palmas del Socorro",
    (68, 533): "Páramo", (68, 547): "Piedecuesta", (68, 549): "Pinchote",
    (68, 572): "Puente Nacional", (68, 573): "Puerto Parra", (68, 575): "Puerto Wilches",
    (68, 615): "Rionegro", (68, 655): "Sabana de Torres", (68, 669): "San Andrés",
    (68, 673): "San Benito", (68, 679): "San Gil", (68, 682): "San Joaquín",
    (68, 684): "San José de Miranda", (68, 686): "San Miguel",
    (68, 689): "San Vicente de Chucurí", (68, 705): "Santa Bárbara",
    (68, 720): "Santa Helena del Opón", (68, 745): "Simacota",
    (68, 755): "Socorro", (68, 770): "Suaita", (68, 773): "Sucre",
    (68, 780): "Suratá", (68, 820): "Tona", (68, 855): "Valle de San José",
    (68, 861): "Vélez", (68, 867): "Vetas", (68, 872): "Villanueva",
    (68, 895): "Zapatoca",
    # Sucre (70)
    (70, 1): "Sincelejo", (70, 110): "Buenavista", (70, 124): "Caimito",
    (70, 204): "Coloso", (70, 215): "Corozal", (70, 221): "Coveñas",
    (70, 230): "Chalán", (70, 233): "El Roble", (70, 235): "Galeras",
    (70, 255): "Guaranda", (70, 400): "La Unión", (70, 418): "Los Palmitos",
    (70, 429): "Majagual", (70, 473): "Morroa", (70, 508): "Ovejas",
    (70, 523): "Palmito", (70, 670): "Sampués", (70, 678): "San Benito Abad",
    (70, 682): "San Juan de Betulia", (70, 702): "San Marcos",
    (70, 708): "San Onofre", (70, 713): "San Pedro", (70, 717): "San Luis de Sincé",
    (70, 742): "Since", (70, 771): "Sucre", (70, 820): "Tolú Viejo",
    (70, 823): "San Antonio de Palmito", (70, 828): "Tolú",
    # Tolima (73)
    (73, 1): "Ibagué", (73, 24): "Alpujarra", (73, 26): "Alvarado",
    (73, 30): "Ambalema", (73, 43): "Anzoátegui", (73, 55): "Armero",
    (73, 67): "Ataco", (73, 124): "Cajamarca", (73, 148): "Carmen de Apicala",
    (73, 152): "Casabianca", (73, 168): "Chaparral", (73, 200): "Coello",
    (73, 217): "Coyaima", (73, 226): "Cunday", (73, 236): "Dolores",
    (73, 268): "Espinal", (73, 270): "Falan", (73, 275): "Flandes",
    (73, 283): "Fresno", (73, 319): "Guamo", (73, 347): "Herveo",
    (73, 349): "Honda", (73, 352): "Icononzo", (73, 408): "Lérida",
    (73, 411): "Líbano", (73, 443): "Mariquita", (73, 449): "Melgar",
    (73, 461): "Murillo", (73, 483): "Natagaima", (73, 504): "Ortega",
    (73, 520): "Palocabildo", (73, 547): "Piedras", (73, 555): "Planadas",
    (73, 563): "Prado", (73, 585): "Purificación", (73, 616): "Rioblanco",
    (73, 622): "Roncesvalles", (73, 624): "Rovira", (73, 671): "Saldaña",
    (73, 675): "San Antonio", (73, 678): "San Luis", (73, 686): "Santa Isabel",
    (73, 770): "Suárez", (73, 854): "Valle de San Juan", (73, 861): "Venadillo",
    (73, 870): "Villahermosa", (73, 873): "Villarrica",
    # Valle del Cauca (76)
    (76, 1): "Cali", (76, 20): "Alcalá", (76, 36): "Andalucía",
    (76, 41): "Ansermanuevo", (76, 54): "Argelia", (76, 100): "Bolívar",
    (76, 109): "Buenaventura", (76, 111): "Guadalajara de Buga",
    (76, 113): "Bugalagrande", (76, 122): "Caicedonia", (76, 126): "Calima",
    (76, 130): "Candelaria", (76, 147): "Cartago", (76, 233): "Dagua",
    (76, 243): "El Águila", (76, 246): "El Cairo", (76, 248): "El Cerrito",
    (76, 250): "El Dovio", (76, 275): "Florida", (76, 306): "Ginebra",
    (76, 318): "Guacarí", (76, 364): "Jamundí", (76, 377): "La Cumbre",
    (76, 400): "La Unión", (76, 403): "La Victoria", (76, 497): "Obando",
    (76, 520): "Palmira", (76, 563): "Pradera", (76, 606): "Restrepo",
    (76, 616): "Riofrío", (76, 622): "Roldanillo", (76, 670): "San Pedro",
    (76, 736): "Sevilla", (76, 823): "Toro", (76, 828): "Trujillo",
    (76, 834): "Tuluá", (76, 845): "Ulloa", (76, 863): "Versalles",
    (76, 869): "Vijes", (76, 890): "Yotoco", (76, 892): "Yumbo",
    (76, 895): "Zarzal",
    # Vaupés (97)
    (97, 1): "Mitú", (97, 161): "Carurú", (97, 511): "Pacoa",
    (97, 666): "Taraira", (97, 777): "Papunaua", (97, 889): "Yavaraté",
    # Vichada (99) - todos los municipios
    (99, 1): "Puerto Carreño", (99, 524): "La Primavera",
    (99, 624): "Santa Rosalía", (99, 773): "Cumaribo",
    # Arauca (81) - ya definido arriba
    # Casanare (85) - ya definido arriba
}

# ══════════════════════════════════════════════════════════════════════════════
# TRANSFORMACIÓN DE EDAD - RANGOS ESTÁRIOS A VALOR NUMÉRICO
# ══════════════════════════════════════════════════════════════════════════════

# Rango etario del Censo 2018 (P_EDADR)
RANGOS_EDAD_DANE = {
    1: {"rango": "00-04", "min": 0, "max": 4, "punto_medio": 2},
    2: {"rango": "05-09", "min": 5, "max": 9, "punto_medio": 7},
    3: {"rango": "10-14", "min": 10, "max": 14, "punto_medio": 12},
    4: {"rango": "15-19", "min": 15, "max": 19, "punto_medio": 17},
    5: {"rango": "20-24", "min": 20, "max": 24, "punto_medio": 22},
    6: {"rango": "25-29", "min": 25, "max": 29, "punto_medio": 27},
    7: {"rango": "30-34", "min": 30, "max": 34, "punto_medio": 32},
    8: {"rango": "35-39", "min": 35, "max": 39, "punto_medio": 37},
    9: {"rango": "40-44", "min": 40, "max": 44, "punto_medio": 42},
    10: {"rango": "45-49", "min": 45, "max": 49, "punto_medio": 47},
    11: {"rango": "50-54", "min": 50, "max": 54, "punto_medio": 52},
    12: {"rango": "55-59", "min": 55, "max": 59, "punto_medio": 57},
    13: {"rango": "60-64", "min": 60, "max": 64, "punto_medio": 62},
    14: {"rango": "65-69", "min": 65, "max": 69, "punto_medio": 67},
    15: {"rango": "70-74", "min": 70, "max": 74, "punto_medio": 72},
    16: {"rango": "75-79", "min": 75, "max": 79, "punto_medio": 77},
    17: {"rango": "80-84", "min": 80, "max": 84, "punto_medio": 82},
    18: {"rango": "85-89", "min": 85, "max": 89, "punto_medio": 87},
    19: {"rango": "90-94", "min": 90, "max": 94, "punto_medio": 92},
    20: {"rango": "95-99", "min": 95, "max": 99, "punto_medio": 97},
    21: {"rango": "100+", "min": 100, "max": 120, "punto_medio": 100},
}

# Grupos de edad amplios para análisis demográfico
GRUPOS_EDAD_AMPLIOS = {
    "Primera infancia (0-9 años)": [1, 2],
    "Niñez (10-14 años)": [3],
    "Adolescencia (15-19 años)": [4],
    "Juventud (20-29 años)": [5, 6],
    "Adultez temprana (30-44 años)": [7, 8, 9],
    "Adultez media (45-59 años)": [10, 11, 12],
    "Adultez mayor (60-74 años)": [13, 14, 15],
    "Vejez (75+ años)": [16, 17, 18, 19, 20, 21],
}


def transformar_edad_rango_a_numero(codigo_rango: int) -> int:
    """
    Transforma un código de rango etario del DANE a un valor numérico único.
    
    Usa el punto medio del rango para análisis estadístico.
    
    Ejemplos:
        1 (00-04) → 2
        4 (15-19) → 17
        10 (45-49) → 47
        21 (100+) → 100
    
    Args:
        codigo_rango: Código del rango etario (1-21)
    
    Returns:
        Punto medio del rango en años
    
    Raises:
        ValueError: Si el código no está en el catálogo DANE
    """
    if codigo_rango not in RANGOS_EDAD_DANE:
        raise ValueError(
            f"Código de rango etario inválido: {codigo_rango}. "
            f"Códigos válidos: 1-21 (catálogo DANE)"
        )
    return RANGOS_EDAD_DANE[codigo_rango]["punto_medio"]


def transformar_numero_a_rango_edad(edad: int) -> dict:
    """
    Transforma una edad numérica a su rango etario correspondiente.
    
    Args:
        edad: Edad en años (0-120)
    
    Returns:
        Diccionario con código, rango y punto medio
    
    Raises:
        ValueError: Si la edad está fuera de rango (0-120)
    """
    if edad < 0 or edad > 120:
        raise ValueError(
            f"Edad inválida: {edad}. Rango aceptado: 0-120 años"
        )
    
    for codigo, datos in RANGOS_EDAD_DANE.items():
        if datos["min"] <= edad <= datos["max"]:
            return {
                "codigo": codigo,
                "rango": datos["rango"],
                "punto_medio": datos["punto_medio"],
            }
    
    # Caso especial: 100+
    return {
        "codigo": 21,
        "rango": "100+",
        "punto_medio": 100,
    }


def obtener_rango_etario_descripcion(codigo: int) -> str:
    """
    Obtiene la descripción textual de un rango etario.
    
    Args:
        codigo: Código del rango (1-21)
    
    Returns:
        Descripción del rango (ej: "de 20 A 24 Años")
    """
    if codigo not in RANGOS_EDAD_DANE:
        return f"Rango inválido ({codigo})"
    
    datos = RANGOS_EDAD_DANE[codigo]
    return f"de {datos['min']:02d} A {datos['max']} Años"


# Funciones de utilidad para conversión de códigos

def obtener_nombre_departamento(codigo: int) -> str:
    """Obtiene el nombre del departamento dado su código DANE."""
    return DEPARTAMENTOS_DANE.get(codigo, f"Desconocido ({codigo})")


def obtener_nombre_sexo(codigo: int) -> str:
    """Obtiene el nombre del sexo dado su código DANE."""
    return SEXO.get(codigo, f"Desconocido ({codigo})")


def obtener_nombre_grupo_etnico(codigo: int) -> str:
    """Obtiene el nombre del grupo étnico dado su código DANE."""
    return GRUPO_ETNICO.get(codigo, f"Desconocido ({codigo})")


def obtener_nombre_estado_civil(codigo: int) -> str:
    """Obtiene el nombre del estado civil dado su código DANE."""
    return ESTADO_CIVIL.get(codigo, f"Desconocido ({codigo})")


def obtener_nombre_trabajo(codigo: int) -> str:
    """Obtiene la descripción de la situación laboral dado su código DANE."""
    return TRABAJO.get(codigo, f"Desconocido ({codigo})")


def obtener_nombre_municipio(dpto: int, mpio: int) -> str:
    """
    Obtiene el nombre del municipio dado su código DIVIPOLA (dpto + mpio).

    Args:
        dpto: Código del departamento (ej: 99 para Vichada)
        mpio: Código del municipio dentro del departamento (ej: 1 para Puerto Carreño)

    Returns:
        Nombre oficial del municipio o código DIVIPOLA si no está en el catálogo.
    """
    nombre = MUNICIPIOS_DANE.get((dpto, mpio))
    if nombre:
        return nombre
    dpto_nombre = DEPARTAMENTOS_DANE.get(dpto, f"Depto {dpto}")
    return f"Mpio {mpio} ({dpto_nombre})"
