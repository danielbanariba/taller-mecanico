#Pagina de "inicio" donde va estar todas las estadisticas y graficas de la empresa
# Aqui abajo voy a dejar algunos links de la documentacion de reflex que se complementa mas con lo que se tiene en figma
# https://reflex.dev/docs/library/graphing/barchart/
# https://reflex.dev/docs/library/graphing/label/

# En este puede ser cualquiera de los dos xd obvio el que se vea mejor
# https://reflex.dev/docs/library/graphing/areachart/
# https://reflex.dev/docs/library/graphing/linechart/

import reflex as rx

#TODO Se tiene que cambiar los datos del arreglo por los datos de la base de datos
data = [
    {"Nombre": "Pagina A", "uv": 4000, "pv": 2400, "amt": 2400},
    {"Nombre": "Pagina B", "uv": 3000, "pv": 1398, "amt": 2210},
    {"Nombre": "Pagina C", "uv": 2000, "pv": 9800, "amt": 2290},
    {"Nombre": "Pagina D", "uv": 2780, "pv": 3908, "amt": 2000},
    {"Nombre": "Pagina E", "uv": 1890, "pv": 4800, "amt": 2181},
    {"Nombre": "Pagina F", "uv": 2390, "pv": 3800, "amt": 2500},
    {"Nombre": "Pagina G", "uv": 3490, "pv": 4300, "amt": 2100},
]

def grafica_de_barras():
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                #              stroke es el color de la linea y fill es el color de la grafica
                data_key="uv", stroke="#8884d8", fill="#8884d8" 
            ),
            rx.recharts.x_axis(data_key="Nombre"),
            rx.recharts.y_axis(),
            # Tamaño de la grafica
            width=600,
            height=300,
            data=data,# Datos que se plasma en la grafica
        )    
    )
    
def grafica_lineal():
    return rx.box(
        rx.recharts.line_chart(
            rx.recharts.line(
                data_key="pv", stroke="#8884d8"
            ),
            rx.recharts.x_axis(data_key="Nombre"),
            rx.recharts.y_axis(),
            # Tamaño de la grafica
            width=600,
            height=300,
            data=data,
        )    
    )
    
def grafica_de_barras_comparable():
    return rx.box(
        rx.recharts.bar_chart(
            rx.recharts.bar(
                data_key="uv", stroke="#8884d8", fill="#8884d8"
            ),
            rx.recharts.bar(
                data_key="pv", stroke="#82ca9d", fill="#82ca9d"
            ),
            rx.recharts.x_axis(data_key="name"),
            rx.recharts.y_axis(),
            width=600,
            height=300,
            data=data,
        )
    )
    
def grafica_de_area():
    return rx.box(
        rx.recharts.area_chart(
            rx.recharts.area(
                data_key="uv", stroke="#8884d8", fill="#8884d8"
            ),
            rx.recharts.x_axis(data_key="name"),
            rx.recharts.y_axis(),
            width=600,
            height=300,
            data=data,
        )
    )