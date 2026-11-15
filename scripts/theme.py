"""Paleta canônica do perfil: base zinc e acento grafite."""
COLOR = {
    'background': '#09090b',
    'card': '#18181b',
    'border': '#27272a',
    'ring': '#3f3f46',
    'line': '#52525b',
    'subtle': '#71717a',
    'muted': '#a1a1aa',
    'foreground': '#fafafa',
    'accent': '#d4d4d8',
    'accent_background': '#242427',
    'lead': '#e4e4e7',
}
# Associação estável por agente, independente da posição no ranking.
AGENT_COLORS = {
    'Claude Code': COLOR['accent'],
    'Codex': COLOR['muted'],
    'Local models': COLOR['subtle'],
    'Other agents': COLOR['foreground'],
}
