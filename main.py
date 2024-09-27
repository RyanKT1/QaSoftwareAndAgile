from website import create_app

app = create_app()

if __name__ == '__main__':
    # change to false when in production , debug = true reruns the webserver whenever a change is made to python code
    app.run()
    # app.run(debug=True,port=5005)
    # To run this website locally uncomment the line above
