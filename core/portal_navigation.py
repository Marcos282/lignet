"""Keep the static homepage usable while Django renders account-aware navigation."""
START = '<!-- SITE_NAVIGATION_START -->'
END = '<!-- SITE_NAVIGATION_END -->'


def replace_navigation(html, navigation):
    if START in html and END in html:
        before, remainder = html.split(START, 1)
        _, after = remainder.split(END, 1)
        return before + START + '\n' + navigation.strip() + '\n' + END + after
    return html.replace('<!-- SITE_NAVIGATION -->', START + '\n' + navigation.strip() + '\n' + END)
