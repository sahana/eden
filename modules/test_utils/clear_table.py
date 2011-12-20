
def clear_table(db, db_table):
    db(db_table.id).delete()
    db.commit()
