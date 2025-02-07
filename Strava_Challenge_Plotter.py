import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import requests
import urllib3
import matplotlib.animation as animation
from Emailer import send_email
from time import sleep

def Get_Keys():

    ID_file_contents = []
    with open("Strava_IDs.txt", "r") as file:
        for line in file:
            line_text = line.split(":")
            for item in line_text:
                ID_file_contents.append(item.strip("\n"))
        file.close()

    strava_payload = {
        'client_id': ID_file_contents[1].strip(" "),
        'client_secret': ID_file_contents[3].strip(" "),
        'refresh_token': ID_file_contents[5].strip(" "),
        'grant_type': "refresh_token",
        'f': 'json'
    }

    email_details = {
        "email_sender": ID_file_contents[7].strip(" "),
        "email_password": ID_file_contents[9],
        "email_receiver": ID_file_contents[11].strip(" ")
    }


    return strava_payload, email_details

def Get_Params():

    today = pd.to_datetime('today').date()
    start_date = pd.Timestamp(year=2025, month=1, day=1).date()
    #start_date = (pd.Timestamp.today()-pd.offsets.YearBegin()).date()
    #end_date = pd.to_datetime(f'{today.year}-12-31').date()
    end_date = pd.Timestamp(year=2025, month=12, day=31).date()
    target = 1000
    duration = ((end_date - start_date).days+1)
    daily_average = target/duration

    params = {
        "activity_type": "Run",
        "start_date": start_date,
        "today": today,
        "end_date": end_date,
        "target": target,
        "daily_average": daily_average,
        "duration": duration
    }

    return params

def Download_Acitivies(strava_payload):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    auth_url = "https://www.strava.com/oauth/token"
    activites_url = "https://www.strava.com/api/v3/athlete/activities"

    print("\nRequesting Strava data: ", end="")
    res = requests.post(auth_url, data=strava_payload, verify=False)
    access_token = res.json()['access_token']

    #print("Access Token = {}".format(access_token))
    header = {'Authorization': 'Bearer ' + access_token}

    # The first loop, request_page_number will be set to one, so it requests the first page. Increment this number after
    # each request, so the next time we request the second page, then third, and so on...
    request_page_num = 1
    all_activities = []

    while True:
        param = {'per_page': 200, 'page': request_page_num}
        # initial request, where we request the first page of activities
        my_dataset = requests.get(activites_url, headers=header, params=param).json()

        # check the response to make sure it is not empty. If it is empty, that means there is no more data left. So if you have
        # 1000 activities, on the 6th request, where we request page 6, there would be no more data left, so we will break out of the loop
        if len(my_dataset) == 0:
            break

        # if the all_activities list is already populated, that means we want to add additional data to it via extend.
        if all_activities:
            all_activities.extend(my_dataset)

        # if the all_activities is empty, this is the first time adding data so we just set it equal to my_dataset
        else:
            all_activities = my_dataset

        request_page_num += 1

    full_data = pd.DataFrame(all_activities)
    print(f"{full_data.shape[0]} activities downloaded")
    return full_data

def Filter_Data(full_data, params):

    print(f"Filtering activities for '{params['activity_type']}' after '{params['start_date']}'")
    #filter out non-runs from the full data array
    non_runs = full_data[full_data["type"] != params['activity_type']].index
    full_data.drop(non_runs, inplace=True)

    #filter out all columns aside from date and distance
    activity_data = full_data[["start_date", "distance"]].copy()

    #rename the columns to match csv file headers
    activity_data = activity_data.rename(columns={"start_date":"Activity Date", "distance":"Distance"})

    #convert dates to datetime format
    activity_data["Activity Date"] = pd.to_datetime(activity_data["Activity Date"]).dt.date

    #remove all data before 1st day of current year
    activity_data = activity_data.loc[(activity_data['Activity Date'] >= params['start_date'])]

    #convert distance to km
    activity_data["Distance"] = round(pd.to_numeric(activity_data["Distance"]/1000), 2)

    print(f"\nFiltered data: \n{activity_data}")

    #add first and last rows (these will be combined if activities already exist for this date)
    #today = pd.Timestamp.today().date()
    activity_data.loc[-1] = [params['today'], 0]
    activity_data.loc[len(activity_data)+1] = [params['start_date'], 0]

    #increment indices and sort by index to move 'today' row to the top of the list
    activity_data.index = activity_data.index + 1
    activity_data.sort_index(inplace=True)

    #combine all activities on same dates
    activity_data = activity_data.groupby("Activity Date", as_index=False)['Distance'].sum()

    #sort by date and reset index
    activity_data = activity_data.sort_values(by="Activity Date").reset_index(drop=True)
    print(f"\nCombining and reorganising:\n{activity_data}")

    return activity_data

def Add_Dates(activity_data):

    print("\nAdding missing rows")
    #initialise loop
    data_complete = True
    while data_complete:
        #set loop to end unless condition is met
        data_complete = False
        new_data = []

        #iterate through activity data until one step from the end
        for i in range(0, activity_data.shape[0]-1):
            #if date of the next activity in the dataframe is not one day later than the current activity, add in a blank date and continue the loop
            if activity_data.loc[i]["Activity Date"] + pd.Timedelta(days=1) != activity_data.loc[i+1]["Activity Date"]:
                new_date = pd.to_datetime(activity_data.loc[i]["Activity Date"] + pd.Timedelta(days=1)).date()
                new_row = [new_date, 0]
                new_data.append(new_row)
                data_complete = True
            else:
                continue

       #convert the new activity to a dataframe and add to activity data, sort the values and reset the index
        if new_data != []:
            new_data = pd.DataFrame(new_data, columns=["Activity Date", "Distance"])
            print(f"New_data: \n{new_data}\n...")
            activity_data = pd.concat(objs=[activity_data, new_data], axis=0).sort_values(by="Activity Date").reset_index(drop=True)

    return activity_data

def Add_Graph_Columns(activity_data, params):

    #add additional columns for cumulative distance and target distance for each row in the dataframe
    cumulative_distance = 0
    cumulative_distance_column = []

    target_distance = 0
    target_distance_column = []

    for i in range(0, activity_data.shape[0]):

        cumulative_distance += activity_data.loc[i]["Distance"]
        cumulative_distance_column.append(cumulative_distance)

        target_distance += round(params["daily_average"], 2)
        target_distance_column.append(target_distance)

    activity_data["Cumulative Distance"] = cumulative_distance_column
    activity_data["Target Distance"] = target_distance_column

    return activity_data

def Plot_Graphs(activity_data, params):

    formatted_dates = []
    #create a new column with the dates formatted as day/month
    for i in range(0, activity_data.shape[0]):
        month = (str(activity_data.loc[i]["Activity Date"]).split(" ")[0].split("-")[1])
        day = (str(activity_data.loc[i]["Activity Date"]).split(" ")[0].split("-")[2])
        new_date = f"{day}-{month}"
        new_date = pd.to_datetime(activity_data.loc[i]["Activity Date"]).date()
        formatted_dates.append(new_date)
    
    activity_data["Date"] = formatted_dates

    
    print("Adding graph columns")
    print(f"\nData ready for plotting:")
    print(activity_data)

    #calculate totals and targets
    distance_run = round(activity_data['Distance'].sum(), 2)
    target_distance_today = round(activity_data.iloc[-1]['Target Distance'], 2)
    days_to_target_date = ((params["end_date"]-params["today"]).days + 1)
    days_elapsed = ((params["today"]-params["start_date"]).days + 1)
    current_average = distance_run / days_elapsed
    new_daily_average = round((params["target"]-distance_run)/days_to_target_date, 2)

    #print out targets
    log = []
    print()
    log.append(f"Your target is to {params['activity_type'].lower()} {params['target']} km in {params['duration']} days, starting on {params['start_date']} and ending on {params['end_date']}.")
    log.append(f"To hit this goal you need to average {round(params['daily_average'], 2)} km per day or {round(params['daily_average']*7, 2)} km per week.")
    log.append(f"As of today you have a total distance of {distance_run} km, to be on target this should be {target_distance_today} km.")

    if target_distance_today-distance_run <= 0:
        log.append(f"You are currently {abs(round(target_distance_today - distance_run, 2))} km ahead of target.")
    else:
        log.append(f"You are currently {abs(round(target_distance_today - distance_run, 2))} km behind target.")
    log.append(f"Your current average is {round(current_average, 2)} km per day, giving you a projection of {round(distance_run + (current_average * days_to_target_date), 2)} km by target date.")
    log.append(f"To hit your target you must now average {new_daily_average} km per day or {round(new_daily_average*7, 2)} km per week.")

    for item in log:
        print(item)

    #print out graphs
    fig, ax = plt.subplots()

    plt.gca().xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%m/%d'))
    plt.gca().xaxis.set_major_locator(matplotlib.dates.AutoDateLocator())
    fig.autofmt_xdate()

    #ani = animation.FuncAnimation(fig=fig, func=update, frames=activity_data.shape[0], interval=500)
    update(activity_data.shape[0])
    ax.set(ylabel="km", xlabel="Date")
    ax.legend()
    #plt.show()
    figure_name = f"{params['today']}.png"
    plt.savefig(figure_name)

    return log, figure_name

def update(frame):

    line1 = plt.plot(activity_data.loc[:frame]["Activity Date"], activity_data.loc[:frame]["Target Distance"], label="Target Distance", color="red")
    line2 = plt.step(activity_data.loc[:frame]["Activity Date"], activity_data.loc[:frame]["Cumulative Distance"], where="post", label=f"Total {params['activity_type']} Distance", color="blue")
    return line1, line2

def Run_Script():

    email_sent = False

    while True:

        hour = pd.to_datetime('today').hour

        if email_sent is False and hour >= 8:

            strava_payload, email_details = Get_Keys()

            params = Get_Params()
            #full_data = pd.read_csv("export_110914245/activities.csv")
            full_data = Download_Acitivies(strava_payload)

            activity_data = Filter_Data(full_data, params)

            activity_data = Add_Dates(activity_data)

            activity_data = Add_Graph_Columns(activity_data, params)

            log, figure_name = Plot_Graphs(activity_data, params)

            print("\nSending email...")
            send_email(email_details, subject=f"Challenge Update - {params['today']}", body=log, image_path=figure_name)
            print("Email sent")

            email_sent = True

            sleep(60*60)

        elif hour < 8 and hour >= 6:

            email_sent = False
            sleep(60*60)

if __name__ == '__main__':
    Run_Script()