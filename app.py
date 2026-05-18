from app import create_app, db, socketio

app = create_app()

if __name__ == '__main__':

    with app.app_context():
        db.create_all()
        print("Database tables created!")

    socketio.run(app, debug=True)
