"""Mede a tipografia dos SVGs gerados, incluindo texto herdado e miniaturas.

Interpreta o subconjunto de CSS e transformações usado neste projeto; não substitui
a inspeção no navegador. Os tamanhos exibidos usam a largura real da imagem.
"""
import re
import xml.etree.ElementTree as ET


def text_metrics(svg, display_width):
    root=ET.fromstring(svg)
    width=float(root.attrib['viewBox'].split()[2])
    css_fonts={}
    for style in root.iter('{http://www.w3.org/2000/svg}style'):
        for selectors, declarations in re.findall(r'([^{}]+)\{([^{}]*)\}',style.text or ''):
            font=re.search(r'\bfont(?:-size)?\s*:[^;{}]*?([\d.]+)px',declarations)
            if font:
                for name in re.findall(r'\.([\w-]+)',selectors):
                    css_fonts[name]=float(font[1])
    rows=[]

    def visit(element, inherited_size=16, inherited_scale=1):
        size=inherited_size
        if 'font-size' in element.attrib:
            size=float(element.attrib['font-size'].removesuffix('px'))
        classes=element.attrib.get('class','').split()
        for name in classes:
            size=css_fonts.get(name,size)
        inline=re.search(r'\bfont(?:-size)?\s*:[^;]*?([\d.]+)px',element.attrib.get('style',''))
        if inline:
            size=float(inline[1])
        scale=inherited_scale
        for x,y in re.findall(r'scale\(\s*([\d.]+)(?:[ ,]+([\d.]+))?\s*\)',element.attrib.get('transform','')):
            scale*=float(y or x)
        if element.tag.endswith('}text'):
            rows.append(dict(text=''.join(element.itertext()),classes=classes,fontSize=size,
                             displayFontSize=size*scale*display_width/width))
        for child in element:
            visit(child,size,scale)

    visit(root)
    return rows
