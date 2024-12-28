from flask import Flask, jsonify,render_template
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from script import setup_driver, login_to_twitter, fetch_trending_topics, print_current_ip, store_in_mongo
import uuid,os
from datetime import datetime


app = Flask(__name__)
socketio = SocketIO(app)
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')
PROXYMESH_AUTH=os.getenv('PROXYMESH_AUTH')
TWITTER_MOBILE=os.getenv('TWITTER_MOBILE')
TWITTER_EMAIL=os.getenv('TWITTER_EMAIL')
TWITTER_PASSWORD=os.getenv('TWITTER_PASSWORD')

@socketio.on('run_script')
def run_script(gui=False):
    unique_id = str(uuid.uuid4())
    try:
        # Step 1: Setup driver
        driver = setup_driver(PROXYMESH_AUTH,gui)
        emit('notification', {'message': "Driver setup completed."})

        # Step 2: Login to Twitter
        login_to_twitter(driver,TWITTER_MOBILE,TWITTER_EMAIL,TWITTER_PASSWORD)
        emit('notification', {'message': "Logged into Twitter."})

        # Step 3: Fetch trending topics
        top_trends = fetch_trending_topics(driver)
        emit('notification', {'message': f"Fetched trending topics"})

        # Step 4: Print current IP
        current_ip = print_current_ip(driver)
        emit('notification', {'message': f"Current IP: {current_ip}"})

        data = {
                "unique_id": unique_id,
                "trends":top_trends,
                "trend1": top_trends[0] if len(top_trends) > 0 else "None",
                "trend2": top_trends[1] if len(top_trends) > 1 else "None",
                "trend3": top_trends[2] if len(top_trends) > 2 else "None",
                "trend4": top_trends[3] if len(top_trends) > 3 else "None",
                "trend5": top_trends[4] if len(top_trends) > 4 else "None",
                "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ip_address": current_ip,
            }
        

        # Step 5: Store trends in MongoDB
        store_in_mongo(data,MONGO_URI,DB_NAME,COLLECTION_NAME)
        emit('notification', {'message': "Trends stored in MongoDB."})

        # Cleanup
        driver.quit()
        if '_id' in data:
            del data['_id']
        for key, value in data.items():
            print(f"Key: {key}, Type: {type(value)}, Value: {value}")
        emit('notification', {'message': "Driver closed."})
        emit('script_complete', {"data":data})

    except Exception as e:
        emit('error', {'message': str(e)})
        print(e)
        driver.quit()


@app.route('/')
def home():
    return render_template('index.html')
    # return jsonify(message="Welcome to the Flask server!")

if __name__ == '__main__':
    app.run(debug=True)