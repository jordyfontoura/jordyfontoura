"""Companheiro C1 com visor de terminal e gesto de confirmação."""

DESCRIPTION = ('Companheiro de código com visor de terminal, antena e três luzes. '
               'O visor alterna o prompt e um sinal de confirmação. '
               'Movimento contínuo discreto; respeita a preferência por movimento reduzido.')
STATIC_DESCRIPTION = 'Companheiro de código com visor de terminal e três luzes acesas, sem animação.'


def artwork(cx, cy, scale):
    """Posiciona o desenho em coordenadas próprias, sem mover texto do banner."""
    return f'''<g class="companion" transform="translate({cx-100*scale:g} {cy-80*scale:g}) scale({scale:g})">
      <ellipse class="companion-shadow" cx="100" cy="144" rx="25" ry="2"/>
      <g class="companion-idle">
        <g transform="translate(100 43)">
          <g class="companion-aerial">
            <circle class="companion-halo" cx="0" cy="-18" r="9"/>
            <path class="companion-mast" d="M0 -14V0"/>
            <rect class="companion-antenna" x="-4" y="-22" width="8" height="8" rx="1"/>
          </g>
        </g>
        <path class="companion-outline" d="M68 43H132V54H146V103H132V114H68V103H54V54H68Z"/>
        <rect class="companion-screen" x="65" y="57" width="70" height="36" rx="2"/>
        <g class="companion-command">
          <path class="companion-prompt" d="M77 67L86 75L77 83"/>
          <path class="companion-cursor" d="M98 83H117"/>
        </g>
        <path class="companion-confirmation" d="M81 75L93 85L119 65"/>
        <rect class="companion-stage companion-context" x="78" y="101" width="12" height="3" rx="1"/>
        <rect class="companion-stage companion-tools" x="96" y="101" width="12" height="3" rx="1"/>
        <rect class="companion-stage companion-product" x="114" y="101" width="12" height="3" rx="1"/>
        <path class="companion-detail" d="M54 73H44V99 M146 73H156V99 M68 114V130H83 M132 114V130H117"/>
      </g>
    </g>'''


def stylesheet(colors):
    """O personagem flutua e alterna o visor; o estado parado mostra o prompt."""
    return f'''
    .companion {{ fill:none; stroke-linecap:round; stroke-linejoin:round; }}
    .companion-outline {{ stroke:{colors['lead']}; stroke-width:1.8; }}
    .companion-screen {{ fill:{colors['background']}; stroke:{colors['subtle']}; stroke-width:1.4; }}
    .companion-detail,.companion-mast {{ stroke:{colors['muted']}; stroke-width:1.6; }}
    .companion-prompt,.companion-cursor,.companion-confirmation {{ stroke:{colors['foreground']}; stroke-width:2.5; }}
    .companion-shadow {{ fill:{colors['subtle']}; opacity:.35; animation:companion-shadow 6.4s ease-in-out infinite; }}
    .companion-idle {{ transform-box:view-box; animation:companion-idle 6.4s ease-in-out infinite; }}
    .companion-aerial {{ transform-box:view-box; transform-origin:0px 0px; animation:companion-aerial 6.4s ease-in-out .18s infinite; }}
    .companion-antenna {{ fill:{colors['accent']}; animation:companion-receive 6.4s ease-in-out infinite; }}
    .companion-halo {{ fill:{colors['accent']}; opacity:.07; }}
    .companion-command {{ animation:companion-command 6.4s steps(1,end) infinite; }}
    .companion-confirmation {{ opacity:0; animation:companion-confirmation 6.4s steps(1,end) infinite; }}
    .companion-cursor {{ animation:companion-cursor 6.4s steps(1,end) infinite; }}
    .companion-stage {{ fill:{colors['accent']}; }}
    .companion-context {{ animation:companion-context 6.4s linear infinite; }}
    .companion-tools {{ animation:companion-tools 6.4s linear infinite; }}
    .companion-product {{ animation:companion-product 6.4s linear infinite; }}
    @keyframes companion-idle {{ 0%,100% {{ transform:translateY(0px); }} 50% {{ transform:translateY(-5px); }} }}
    @keyframes companion-shadow {{ 0%,100% {{ opacity:.35; }} 50% {{ opacity:.18; }} }}
    @keyframes companion-aerial {{ 0%,100% {{ transform:rotate(0deg); }} 20% {{ transform:rotate(-2deg); }} 60% {{ transform:rotate(3deg); }} }}
    @keyframes companion-receive {{ 0%,47%,100% {{ opacity:.6; }} 50%,64% {{ opacity:1; }} 67% {{ opacity:.6; }} }}
    @keyframes companion-command {{ 0%,49.99%,65%,100% {{ opacity:1; }} 50%,64.99% {{ opacity:0; }} }}
    @keyframes companion-confirmation {{ 0%,49.99%,65%,100% {{ opacity:0; }} 50%,64.99% {{ opacity:1; }} }}
    @keyframes companion-cursor {{ 0%,69.99%,72%,100% {{ opacity:1; }} 70%,71.99% {{ opacity:0; }} }}
    @keyframes companion-context {{ 0%,9%,98%,100% {{ opacity:.25; }} 10%,90% {{ opacity:1; }} }}
    @keyframes companion-tools {{ 0%,29%,98%,100% {{ opacity:.25; }} 30%,90% {{ opacity:1; }} }}
    @keyframes companion-product {{ 0%,49%,98%,100% {{ opacity:.25; }} 50%,90% {{ opacity:1; }} }}'''
