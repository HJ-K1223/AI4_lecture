from django.db import migrations

RELATIONS = [("posts", "author_id", "members", "RESTRICT"),
             ("comments", "author_id", "members", "RESTRICT"),
             ("comments", "post_id", "posts", "CASCADE"),
             ("banned_terms", "created_by_id", "members", "SET NULL")]

def configure(schema_editor, reverse=False):
    q = schema_editor.quote_name
    with schema_editor.connection.cursor() as cursor:
        for table, column, parent, action in RELATIONS:
            constraints = schema_editor.connection.introspection.get_constraints(cursor, table)
            for name, info in constraints.items():
                if info.get("foreign_key") and info["columns"] == [column]:
                    cursor.execute(f"ALTER TABLE {q(table)} DROP CONSTRAINT {q(name)}")
                    selected = "NO ACTION" if reverse else action
                    cursor.execute(f"ALTER TABLE {q(table)} ADD CONSTRAINT {q(name)} FOREIGN KEY ({q(column)}) REFERENCES {q(parent)} (id) ON DELETE {selected} DEFERRABLE INITIALLY DEFERRED")

def forwards(apps, schema_editor):
    configure(schema_editor)

def backwards(apps, schema_editor):
    configure(schema_editor, reverse=True)

class Migration(migrations.Migration):
    dependencies = [("moderation", "0001_initial"), ("board", "0001_initial")]
    operations = [migrations.RunPython(forwards, backwards)]

