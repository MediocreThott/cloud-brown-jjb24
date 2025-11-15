# File: gbmodel/__init__.py

# Set the model_backend to 'datastore' to use our modified file.
model_backend = 'datastore'

if model_backend == 'datastore':
    from .model_datastore import model
elif model_backend == 'sqlite3':
    # This is kept for local testing if you ever need it.
    from .model_sqlite3 import model
else:
    raise ValueError("No appropriate databackend configured.")

appmodel = model()

def get_model():
    return appmodel
