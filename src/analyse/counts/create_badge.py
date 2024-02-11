def create_badge(status: str) -> str:
    colors = {
        'no data': '#a1a1a1',
        'error': '#8c0a8c',
        'pending': '#1e1ef6',
        'overdue': '#ef2626',
        'partial': '#efbf21',
        'completed': '#1aa616',
    }
    return (
        f'<div style='
        f'"background-color: {colors[status]}; '
        f'color: #fff;'
        f'display: inline; '
        f'padding: 0.2em 0.6em '
        f'0.3em;'
        f'font-size:75%;'
        f'font-weight: 700;'
        f'line-height: 1;'
        f'text-align: center;'
        f'white-space: nowrap;'
        f'vertical-align: baseline;'
        f'border-radius: 0.25em;'
        f'font-family: muli,helvetica,Arial,sans-serif;'
        f'margin: auto;">'
        f'{status}'
        f'</div>')
