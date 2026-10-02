"""Brand color mapping and CSS injection helpers."""

BRAND_COLORS = {
    "portfolio": {"bg": "#0F172A", "text": "#FFFFFF", "accent": "#38BDF8"},
    "gymos": {"bg": "#1F4E78", "text": "#FFFFFF", "accent": "#22C55E"},
    "webscraper": {"bg": "#1F4E78", "text": "#FFFFFF", "accent": "#22C55E"},
}

BRAND_DISPLAY = {
    "portfolio": "Abhilash Singh Rajput",
    "gymos": "GymOS",
    "webscraper": "Web Scraper Studio",
}

BRAND_SITES = {
    "portfolio": "abhilash.dev",
    "gymos": "bodycare-gym.vercel.app",
    "webscraper": "webscraperstudio.vercel.app",
}


def inject_brand_css(html: str, brand: str) -> str:
    """Insert CSS overrides for the brand's colors before </head> (fallback </style>/append).

    Returns modified html with :root variable overrides so templates render
    in exact brand colors regardless of brand_base.css defaults.
    """
    key = (brand or "").strip().lower()
    colors = BRAND_COLORS.get(key)
    if not colors:
        return html
    override = (
        "<style>\n"
        ":root {\n"
        f"  --brand-bg: {colors['bg']};\n"
        f"  --brand-accent: {colors['accent']};\n"
        f"  --brand-text: {colors['text']};\n"
        "  --brand-text-muted: rgba(255,255,255,0.7);\n"
        "}\n"
        "</style>"
    )
    if "</head>" in html:
        return html.replace("</head>", override + "\n</head>", 1)
    if "</style>" in html:
        # Insert after first closing style tag.
        return html.replace("</style>", "</style>\n" + override, 1)
    return html + "\n" + override
