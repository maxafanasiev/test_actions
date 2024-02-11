def create_button(cell, url):
    if "nan" == cell:
        return ""
    return f'<a href="{url}" style="color: #0066cc; text-decoration: none; font-weight: bold;">{cell}</a>'

