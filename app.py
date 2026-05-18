from app import create_app, db, socketio

app = create_app()


with app.app_context():
    db.create_all()
    print("Database tables created!")

# Run locally only
if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )