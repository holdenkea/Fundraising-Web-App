from website import create_app     # we can do this because website is a python package and run everyting in init.py

app = create_app()

if __name__ == '__main__':         # only if we run file not import, are we going to execute the line
    app.run(host="0.0.0.0", port=5000, debug=True)            # runs flask application, debug=True means everytime we make a change
                                   # to our python code, it will rerun the web server, turn off when running in production
