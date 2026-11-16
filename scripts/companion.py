"""Companheiro de código: silhueta C1, visor de terminal e movimento de espera."""


def artwork(cx, cy, scale):
    """Posiciona o desenho em coordenadas próprias, sem mover texto do banner."""
    return f'''<g class="companion" transform="translate({cx-100*scale:g} {cy-80*scale:g}) scale({scale:g})">
      <path class="companion-ground" d="M38 147H162"/>
      <path class="companion-shadow" d="M75 153H125"/>
      <g class="companion-idle">
        <circle class="companion-halo" cx="100" cy="25" r="9"/>
        <path class="companion-mast" d="M100 29V43"/>
        <rect class="companion-antenna" x="96" y="21" width="8" height="8" rx="1"/>
        <path class="companion-outline" d="M68 43H132V54H146V103H132V114H68V103H54V54H68Z"/>
        <rect class="companion-screen" x="65" y="57" width="70" height="36" rx="2"/>
        <path class="companion-prompt" d="M77 67L86 75L77 83"/>
        <path class="companion-cursor" d="M98 83H117"/>
        <path class="companion-detail" d="M79 103H95 M102 103H121 M54 73H44V99 M146 73H156V99 M68 114V130H83 M132 114V130H117"/>
      </g>
    </g>'''


def stylesheet(colors):
    """Os três gestos são contínuos, lentos e independentes da digitação do banner."""
    return f'''
    .companion {{ fill:none; stroke-linecap:round; stroke-linejoin:round; }}
    .companion-outline {{ stroke:{colors['lead']}; stroke-width:1.8; }}
    .companion-screen {{ fill:{colors['background']}; stroke:{colors['subtle']}; stroke-width:1.4; }}
    .companion-detail,.companion-mast {{ stroke:{colors['muted']}; stroke-width:1.6; }}
    .companion-prompt,.companion-cursor {{ stroke:{colors['foreground']}; stroke-width:2.5; }}
    .companion-ground {{ stroke:{colors['ring']}; stroke-width:1; }}
    .companion-shadow {{ stroke:{colors['subtle']}; stroke-width:2; opacity:.5; animation:companion-shadow 6.4s ease-in-out infinite; }}
    .companion-idle {{ transform-origin:100px 85px; animation:companion-idle 6.4s ease-in-out infinite; }}
    .companion-antenna {{ fill:{colors['accent']}; animation:companion-receive 4.8s ease-in-out infinite; }}
    .companion-halo {{ fill:{colors['accent']}; opacity:.07; }}
    .companion-cursor {{ animation:companion-cursor 3.2s ease-in-out infinite; }}
    @keyframes companion-idle {{
      0%,100% {{ transform:translateY(0px) rotate(-1deg); }}
      50% {{ transform:translateY(-4px) rotate(1deg); }}
    }}
    @keyframes companion-shadow {{ 0%,100% {{ opacity:.5; }} 50% {{ opacity:.25; }} }}
    @keyframes companion-receive {{ 0%,100% {{ opacity:.55; }} 40% {{ opacity:1; }} }}
    @keyframes companion-cursor {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:.4; }} }}'''
