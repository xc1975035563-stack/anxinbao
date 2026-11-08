from app.main import app

lines = [f"{type(route).__name__} {getattr(route, 'path', '?')}" for route in app.routes]
print("\n".join(lines))
