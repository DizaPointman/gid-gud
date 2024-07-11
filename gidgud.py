from app.factory import create_app

# Startup Check
print("Starting the application...")

# Create the Flask application instance
app = create_app()

if __name__ == "__main__":
    # Run the Flask application
    app.run()