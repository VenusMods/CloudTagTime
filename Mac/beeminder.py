import requests
import json
import time
import re
from datetime import datetime

# GET Request
def get_username(auth_token):
    # URL and parameters
    url = f"https://www.beeminder.com/api/v1/users/me.json"

    # Make the GET request
    response = requests.get(url, params={"auth_token": auth_token})

    # Check if the request was successful
    if response.status_code == 200:
        # Print the JSON response
        data = response.json()
        return data['username']
    else:
        print(f"Request failed with status code {response.status_code}")
        return False

# GET Request
def get_all_goals(auth_token):
    # URL and parameters
    url = f"https://www.beeminder.com/api/v1/users/me/goals.json"

    # Make the GET request
    response = requests.get(url, params={"auth_token": auth_token})

    # Check if the request was successful
    if response.status_code == 200:
        # Print the JSON response
        data = response.json()
        # print(data)
        goals = []
        for item in data:
            goals.append(item['slug'])
        return goals
    else:
        print(f"Request failed with status code {response.status_code}")
        return False

# GET Request
def get_goal_datapoints(auth_token, goal):
    # URL and parameters
    url = f"https://www.beeminder.com/api/v1/users/me/goals/{goal}/datapoints.json"

    # Make the GET request
    response = requests.get(url, params={"auth_token": auth_token})

    # Check if the request was successful
    if response.status_code == 200:
        # Print the JSON response
        data = response.json()
        print(data)
        return data
        # for item in data:
        #     print(item['timestamp'], item['comment'], item['id'], item['fulltext'])
    else:
        print(f"Request failed with status code {response.status_code}")

# PUT Request
def update_datapoint(auth_token, goal, tags, id, value):
    # URL and parameters
    url = f"https://www.beeminder.com/api/v1/users/me/goals/{goal}/datapoints/{id}.json"
    print(url)

    # Data to be sent in the POST request
    data = {
        "auth_token": auth_token,
        "comment": tags,
        "value": value
    }

    # Make the POST request
    response = requests.put(url, data=data)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the JSON response
        data = response.json()
        print(data)
    else:
        print(f"Request failed with status code {response.status_code}")

# PUT Request
def log_update_datapoint(auth_token, goal, timestamp, old_words, new_words):

    print("LOG UPDATE DATAPOINT")

    data = get_goal_datapoints(auth_token, goal)
    fulltext = ""

    for item in data:
        print(item['timestamp'], item['comment'], item['id'], item['fulltext'], item['value'])
        fulltext1 = item['fulltext']
        prev_tag = item['comment']
        prev_id = item['id']
        prev_value = float(item['value'])
        unix_timestamp = int(item['timestamp'])

        date_part = fulltext1.split()[0]

        # Convert the string date to a datetime object
        parsed_date = datetime.strptime(date_part, "%Y-%b-%d").date()

        same_date = datetime.fromtimestamp(timestamp).date()

        if parsed_date == same_date:
            if old_words in prev_tag:
                fulltext = "full!"
                break
            else:
                print("same datapoint id, but different tags, making new ones")
                final_tag = f"1 ping: {new_words}"

                update_datapoint(auth_token, goal, final_tag, prev_id, prev_value)
                return

    if fulltext:

        print(prev_tag)
        print(old_words, " old words")
        print(new_words, " new words")
        new_string = prev_tag.replace(old_words, new_words)
        print(new_string, " new_string")

        final_tag = f"{new_string}"

        update_datapoint(auth_token, goal, final_tag, prev_id, prev_value)
        return
    
    else:
        print("no matching datapoint id")

# POST Request
def create_datapoint(auth_token, timestamp, goal, tags, gap_value):

    data = get_goal_datapoints(auth_token, goal)
    fulltext = ""

    for item in data:
        print(item['timestamp'], item['comment'], item['id'], item['fulltext'], item['value'])
        fulltext1 = item['fulltext']
        prev_tag = item['comment']
        prev_id = item['id']
        prev_value = float(item['value'])
        unix_timestamp = int(item['timestamp'])

        date_part = fulltext1.split()[0]

        # Convert the string date to a datetime object
        parsed_date = datetime.strptime(date_part, "%Y-%b-%d").date()

        today = datetime.fromtimestamp(timestamp).date()

        weekly_border = int(time.time()) - 604800

        if parsed_date == today:
            fulltext = item['fulltext']
            break
        elif unix_timestamp < weekly_border:
            print("No datapoint for given day")
            break

    if fulltext:
        date_part = fulltext.split()[0]

        # Convert the string date to a datetime object
        parsed_date = datetime.strptime(date_part, "%Y-%b-%d").date()

        today = datetime.fromtimestamp(timestamp).date()

        print(parsed_date, " parsed datee")
        print(today, " today")
        if parsed_date == today:
            print("The date is today! should update the datapoint with id of latest ping")
            print("I need auth_token, goal, tags, id")

            print(prev_tag)
            if ':' in prev_tag:
                try:
                    ping_count = prev_tag.split(":", 1)[0].strip()
                    ping_num, ping_str = ping_count.split(" ")
                    new_ping_num = int(ping_num) + 1
                    if ping_str == 'ping':
                        ping_str = 'pings'
                    new_ping_count = f"{new_ping_num} {ping_str}:"
                    remaining_text = prev_tag.split(":", 1)[1].strip()
                    new_prev_tag = f"{new_ping_count} {remaining_text}"
                    print(new_prev_tag)
                except Exception as e:
                    print(e)
                    print("start of datapoint does not have <int> ping(s): but it does have something with a colon, revert to 2 pings: datapoint")
                    new_ping_count = "2 pings:"
                    new_prev_tag = f"{new_ping_count} {prev_tag}"
            else:
                new_ping_count = "2 pings:"
                new_prev_tag = f"{new_ping_count} {prev_tag}"

            final_tag = f"{new_prev_tag}, {tags}"

            new_value = prev_value + gap_value

            update_datapoint(auth_token, goal, final_tag, prev_id, new_value)
            return
        else:
            print("The date is not today.")
            pass

    # URL and parameters
    url = f"https://www.beeminder.com/api/v1/users/me/goals/{goal}/datapoints.json"
    print(url)

    # Data to be sent in the POST request
    data = {
        "auth_token": auth_token,
        "timestamp": timestamp,
        "value": gap_value,
        "comment": f"1 ping: {tags}"
    }

    # Make the POST request
    response = requests.post(url, data=data)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the JSON response
        data = response.json()
        print(data)
        print(timestamp)
    else:
        print(f"Request failed with status code {response.status_code}")

# POST Request
def create_multiple_datapoints(auth_token, goal, datapoints):
    # URL and parameters
    url = f"https://www.beeminder.com/api/v1/users/me/goals/{goal}/datapoints/create_all.json"
    print(url)

    # Data to be sent in the POST request
    data = {
        "auth_token": auth_token,
        "datapoints": json.dumps(datapoints)
    }

    # Make the POST request
    response = requests.post(url, data=data)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the JSON response
        data = response.json()
        print(data)
    else:
        print(f"Request failed with status code {response.status_code}")

# PUT Request
def update_multiple_datapoints(auth_token, goal, datapoints):
    # URL and parameters
    url = f"https://www.beeminder.com/api/v1/users/me/goals/{goal}/datapoints/update_all.json"
    print(url)

    # Data to be sent in the POST request
    data = {
        "auth_token": auth_token,
        "datapoints": json.dumps(datapoints)
    }

    # Make the POST request
    response = requests.put(url, data=data)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the JSON response
        data = response.json()
        print(data)
    else:
        print(f"Request failed with status code {response.status_code}")

# DELETE Request
def delete_datapoint(auth_token, goal, id):
    # URL and parameters
    url = f"https://www.beeminder.com/api/v1/users/me/goals/{goal}/datapoints/{id}.json"
    print(url)

    # Data to be sent in the POST request
    data = {
        "auth_token": auth_token
    }

    # Make the POST request
    response = requests.delete(url, data=data)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the JSON response
        data = response.json()
        print(data)
    else:
        print(f"Request failed with status code {response.status_code}")

# DELETE Request
def log_delete_datapoint(auth_token, goal, timestamp, old_words, gap_value):

    print("LOG DELETE DATAPOINT")

    data = get_goal_datapoints(auth_token, goal)
    fulltext = ""

    for item in data:
        print(item['timestamp'], item['comment'], item['id'], item['fulltext'], item['value'])
        fulltext1 = item['fulltext']
        prev_tag = item['comment']
        prev_id = item['id']
        prev_value = float(item['value'])
        unix_timestamp = int(item['timestamp'])

        date_part = fulltext1.split()[0]

        # Convert the string date to a datetime object
        parsed_date = datetime.strptime(date_part, "%Y-%b-%d").date()

        same_date = datetime.fromtimestamp(timestamp).date()

        if parsed_date == same_date:
            if old_words in prev_tag:
                fulltext = "full!"
                break
            else:
                print("same datapoint id, but different tags, deleting whole comment")
                print(" DELETING DATAPOINT 1")
                delete_datapoint(auth_token, goal, prev_id)
                return

    if fulltext:

        if ':' in prev_tag:
            try:
                ping_count = prev_tag.split(":", 1)[0].strip()
                ping_num, ping_str = ping_count.split(" ")
                new_ping_num = int(ping_num) - 1
            except Exception as e:
                print(e)
                new_ping_num = 0
            if new_ping_num == 1:
                ping_str = 'ping'
            if new_ping_num < 1:
                print(" DELETING DATAPOINT 2")
                delete_datapoint(auth_token, goal, prev_id)
                return
            new_ping_count = f"{new_ping_num} {ping_str}:"
            remaining_text = prev_tag.split(":", 1)[1].strip()
            prev_tag = f"{new_ping_count} {remaining_text}"
            print(prev_tag)
        else:
            print(" DELETING DATAPOINT 3")
            delete_datapoint(auth_token, goal, prev_id)
            return

        new_value = prev_value - gap_value

        print(prev_tag)
        print(old_words, " old words")
        # Regular expression to match the remove_string and any previous comma
        pattern = r'(,\s?' + re.escape(old_words) + r'|'+ re.escape(old_words) + r',\s?)'

        # Remove the matched part from the string
        result = re.sub(pattern, '', prev_tag).strip()

        print(result, " new_string")

        update_datapoint(auth_token, goal, result, prev_id, new_value)
        return
    
    else:
        print("no matching datapoint id")
