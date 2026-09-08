def analyze_html(html):
    suggestions = []

    if "button" in html and "style" not in html:
        suggestions.append("Consider adding button styling")

    if "<input" in html and "label" not in html:
        suggestions.append("Missing labels for accessibility")

    if "div" in html:
        suggestions.append("Check mobile responsiveness")

    return suggestions
