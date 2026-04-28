# run.py is the ENTRY POINT of the application
# This is the file that run to start the Finlytic web server

from app import create_app  # Import the factory function that builds Flask app

# Call create_app() to initialize Flask with all settings, extensions, and blueprints
app = create_app()

# This block only runs when you execute: python run.py
# It does NOT run when Flask imports this file internally
if __name__ == '__main__':
    # Start the development web server
    # debug=True means:
        # - Auto-reloads the server when you change code
        # - Shows detailed error pages in the browser
        # - Should NEVER be True in a real production deployment
    app.run(debug=True, host='127.0.0.1', port=5000)