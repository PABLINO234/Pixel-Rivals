# Pixel Rivals 2.2

Arcade local para dos jugadores, pensado para Raspberry Pi 3B+.

## Controles
- Jugador 1: WASD para moverse, F para dash.
- Jugador 2: flechas para moverse, Ctrl derecho para dash.
- Enter: iniciar / nueva partida.
- Esc: pausa.
- Espacio: continuar.
- R: reiniciar.

## Mecánicas
- Partidas de **60 segundos**.
- Monedas, gemas y estrellas con distintos puntajes.
- Combos: recogé objetos en menos de 2,5 segundos para duplicar puntos; desde la tercera recogida hay bonus.
- Dash: impulso rápido con 4 segundos de recarga.
- Boost: aumenta temporalmente la velocidad.
- Imán: atrae coleccionables.
- Multiplicador x2 y escudo.
- Congelación: un coleccionable congela al rival durante 1,8 segundos.
- Minas móviles: restan 15 puntos y ralentizan; el escudo bloquea el impacto.
- Portales: dos puntos de teletransporte, con 3 segundos de recarga individual.
- Sobrecarga dorada: eventos temporales que duplican puntos.
- Recta final: durante los últimos 10 segundos, los coleccionables valen el doble.
- Efectos de partículas, cuenta regresiva y pantalla de ganador.

## Ejecutar en Windows
```powershell
py -3.15 -m pip install pygame-ce
py -3.15 main.py
```

## Ejecutar en Raspberry Pi OS
```bash
sudo apt update
sudo apt install -y python3-pygame
python3 main.py
```

No necesita internet ni archivos multimedia externos.
