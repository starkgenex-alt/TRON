# fallback helpers for simple http.server streaming if needed

def sse_format(event):
    return f"data: {event}\n\n"

