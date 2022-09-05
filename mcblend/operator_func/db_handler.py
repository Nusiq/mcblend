from pathlib import Path
from sqlite3 import Connection
from .sqlite_bedrock_packs import load_rp, create_db
from functools import cache

@cache
def get_db() -> Connection:
    '''Singleton for the database'''
    return create_db()

def delete_db():
    '''Delete all data from the database.'''
    db = get_db()
    db.execute('DELETE FROM ResourcePack;')

def load_resource_pack(path: Path):
    '''Load a resource pack into the database'''
    db = get_db()
    load_rp(
        db, path,
        selection_mode='include',
        client_entities=True,
        attachables=True,
        geometries=True,
        render_controllers=True,
        textures=True,
    )
