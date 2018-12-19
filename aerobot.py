import telebot
from datetime import datetime
from telebot import types
import sqlite3
import time
import random
from numpy.linalg import solve
import math
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

dbname = 'pythonsqlite.db'

token = '743871695:AAHSQVrNYaqP7icgyRoj9FloT9HDanWUMy8'
bot = telebot.TeleBot(token)

def check_feedback_name(message):
    text = message.text
    if 'name ' in text or 'Name ' in text or 'NAME ' in text:
        return True
    return False

def check_feedback_country(message):
    text = message.text
    if 'country ' in text or 'Country ' in text or 'COUNTRY ' in text:
        return True
    return False

def check_feedback_airline_flight(message):
    text = message.text
    all_airlines, all_flights = get_airlines(), get_flights()
    all_airlines = [a[0] for a in all_airlines]
    text = text.upper()
    tokens = text.split(' ')
    if 'AIRLINE' == tokens[0] and tokens[1] in all_airlines and 'FLIGHT' == tokens[2] and tokens[3] in all_flights:
        return True
    return False

def check_feedback_date(message):
    text = message.text.upper()
    text = text.split(' ')
    if text[0] == 'DATE' and text[1].count('-') == 2:
        return True
    return False

def check_feedback_class(message):
    text = message.text.upper()
    text = text.split(' ')
    first = ['BUSINESS', 'ECONOMY']
    last = ['YES', 'NO']
    if text[0] in first and int(text[1]) in np.arange(1,11) and text[2] in last:
        return True
    return False

def check_feedback_content(message):
    text = message.text.upper()
    text = text.split(' ')
    if 'FEEDBACK' == text[0]:
        return True
    return False

def get_authors():
    new_request = 'SELECT DISTINCT ID_Author FROM Authors'
    conn = sqlite3.connect(dbname)
    conn.text_factory = bytes
    cursor = conn.cursor()
    cursor.execute(new_request)
    results = cursor.fetchall()
    conn.close()
    results_fixed = []
    for res in results:
        try:
            results_fixed.append(res[0].decode('utf8'))
        except:
            continue
    return results_fixed

def fix_zero(num):
    if num == -0.0:
        return 0.0
    else:
        return num

def prepare_list(header, ents):
    out = header + '\n\n'
    for ent in ents:
        out += ent + '\n'
    return out

def request_airline(airline):
    new_request = """SELECT DISTINCT t.ID_flight, t.Airport_dep, t.Airport_ar, ROUND(Delay_Prediction) AS Delay_Prediction, \
    a1.City AS City1, t.Scheduled_departure, a2.City AS City2, t.Scheduled_arrival FROM (SELECT dep.ID_flight, dep.ID_Airport \
    AS Airport_dep, dep.Actual_departure, dep.Scheduled_departure, ar.ID_Airport AS Airport_ar, ar.Actual_arrival, ar.Scheduled_arrival \
    FROM Flights_Airports_dep AS dep INNER JOIN Flights_Airports_ar AS ar ON dep.rowid = ar.rowid) AS t INNER JOIN Flights \
    AS f ON f.ID_Flight = t.ID_Flight INNER JOIN Airports AS a1 ON a1.ID_Airport = t.Airport_dep INNER JOIN Airports \
    AS a2 ON a2.ID_Airport = t.Airport_ar WHERE f.ID_flight LIKE ? GROUP BY f.ID_flight HAVING Delay_prediction <= 0 \
    ORDER BY t.Scheduled_departure DESC LIMIT 10"""
    new_request = new_request.replace('LIKE ?', 'LIKE ' + "'" + airline + "%'")
    conn = sqlite3.connect(dbname)
    cursor = conn.cursor()
    cursor.execute(new_request)
    results = cursor.fetchall()
    conn.close()
    if len(results) == 0:
        return False
    out = 'Flights for ' + airline + ' airline:\n\n'
    for info in results:
        out += 'Flight number: ' + info[0] + '\n' + \
            'Departure city: ' + info[4] + '\n' + \
            'Departure airport: ' + info[1] + '\n' + \
            'Depatrure date and time: ' + fix_time(info[5]) + '\n' + \
            'Arrival city: ' + info[6] + '\n' + \
            'Arrival airport: ' + info[2] + '\n' + \
            'Arrival date and time: ' + fix_time(info[7]) + '\n' + \
            'Delay predict (min): ' + fix_zero(str(info[3]))[:-2] + '\n\n'
    return out

def request_flight(fl_number):
    new_request = """SELECT DISTINCT t.*, ROUND(Delay_Prediction) AS Delay_Prediction, a1.City AS City1, a2.City AS City2, \
    ID_Author, Date, Score, Recommendation, Class, Content FROM (SELECT dep.ID_flight, dep.ID_Airport AS Airport_dep, dep.Scheduled_departure, \
    ar.ID_Airport AS Airport_ar, ar.Scheduled_arrival FROM Flights_Airports_dep AS dep INNER JOIN Flights_Airports_ar AS ar ON dep.rowid = ar.rowid) AS t \
    INNER JOIN Flights AS f ON f.ID_Flight = t.ID_Flight INNER JOIN Airports AS a1 ON a1.ID_Airport = t.Airport_dep INNER JOIN Airports AS \
    a2 ON a2.ID_Airport = t.Airport_ar LEFT JOIN Feedbacks AS r ON f.ID_Flight = r.ID_Flight WHERE t.ID_flight = ? GROUP BY t.Scheduled_departure \
    ORDER BY t.Scheduled_departure DESC LIMIT 1"""
    new_request = new_request.replace('t.ID_flight = ?', 't.ID_flight = ' + "'" + fl_number + "'")
    conn = sqlite3.connect(dbname)
    cursor = conn.cursor()
    cursor.execute(new_request)
    results = cursor.fetchall()
    conn.close()
    if len(results) == 0:
        return False
    out = 'Information about flight ' + fl_number + ':' + '\n\n'
    for info in results:
        out += 'Departure city: ' + info[6] + '\n' + \
            'Departure airport: ' + info[1] + '\n' + \
            'Time and date of departure: ' + fix_time(info[2]) + '\n' + \
            'Destination city: ' + info[7] + '\n' + \
            'Destination airport: ' + info[3] + '\n' + \
            'Time and date of arrival: ' + fix_time(info[4]) + '\n' + \
            'Delay prediction (min): ' + str(fix_zero(info[5]))[:-2] + '\n\n' + \
            'Flight feedback: ' + info[-1] + '\n' + \
            'Flight score (out of 10): ' + str(info[10]) + '\n' + \
            'Flight recommendation: ' + 'Yes' if info[11] else 'No'
    return out

def check_airline(message):
    text = message.text
    new_request = 'select distinct ID_Airline, Airline_name from Airlines'
    conn = sqlite3.connect(dbname)
    cursor = conn.cursor()
    cursor.execute(new_request)
    results = cursor.fetchall()
    conn.close()
    airlines = [res[0] for res in results]
    text_upper = text.upper()
    cur_airline = text_upper.strip().split(' ')[-1]
    if cur_airline in airlines and 'AIRLINE' in text_upper:
        return cur_airline
    else:
        return False

def check_flight(message):
    text = message.text
    new_request = 'SELECT DISTINCT ID_flight FROM Flights'
    conn = sqlite3.connect(dbname)
    cursor = conn.cursor()
    cursor.execute(new_request)
    results = cursor.fetchall()
    conn.close()
    flights = [res[0] for res in results]
    text_upper = text.upper()
    text_upper = text_upper.strip().split(' ')
    cur_flight = text_upper[-1]
    if cur_flight in flights and 'FLIGHT' in text_upper and len(text_upper) == 2:
        return flights
    else:
        return False

def get_airlines():
    new_request = 'select distinct ID_Airline, Airline_name from Airlines'
    conn = sqlite3.connect(dbname)
    cursor = conn.cursor()
    cursor.execute(new_request)
    results = cursor.fetchall()
    conn.close()
    return results

def get_flights():
    conn = sqlite3.connect(dbname)
    cursor = conn.cursor()
    request = 'SELECT DISTINCT ID_flight FROM Flights'
    cursor.execute(request)
    res = cursor.fetchall()
    res = set([i[0] for i in res])
    conn.close()
    return res

def get_beautiful_map(coords, from_city, to_city):
    fig = plt.figure(figsize=(15, 15))
    m = Basemap(projection='lcc',
                width=6E6, height=3E6,
                lat_0=40, lon_0=-100)
    m.etopo(scale=0.5, alpha=0.7)

    x1, y1 = m(coords[1], coords[0])
    x2, y2 = m(coords[3], coords[2])
    leng = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    x_av, y_av = (x1 + x2) / 2 + leng / 10, (y1 + y2) / 2 + leng / 10
    eq_1 = [x1 ** 2, x1, 1]
    eq_2 = [x2 ** 2, x2, 1]
    eq_3 = [x_av ** 2, x_av, 1]
    X = [eq_1, eq_2, eq_3]
    y = [y1, y2, y_av]

    coefs = solve(X, y)

    if x1 > x2:
        x_dots = np.arange(x1, x2, -10)
    else:
        x_dots = np.arange(x1, x2, 10)

    y_dots = []

    for x in x_dots:
        y_dots.append(coefs[0] * x ** 2 + coefs[1] * x + coefs[2])


    plt.plot(x1, y1, 'ok', markersize=8, c='lime', label='Departure city', zorder=3)
    plt.text(x1 + 50000, y1 - 50000, from_city, fontsize=12, zorder=4)

    plt.plot(x2, y2, 'ok', markersize=8, c='tomato', label='Destination city', zorder=2)
    plt.text(x2 + 50000, y2 - 50000, to_city, fontsize=12, zorder=5)

    plt.plot(x_dots, y_dots, linewidth=4, linestyle='--', solid_capstyle='round', c='blue', label='Your trip', zorder=1)
    plt.legend(fontsize='large')
    plt.savefig('map.png', bbox_inches='tight', pad_inches=0)
    return 'map.png'

def fix_time(datetime):
    time = datetime[-5:]
    date = datetime[:10]
    return ' '.join((time, date))

def request_destinations(request, from_city, to_city, c):
    bot.send_chat_action(c.message.chat.id, 'typing')
    conn = sqlite3.connect(dbname)
    cursor = conn.cursor()
    start = time.clock()
    cursor.execute(request)
    print(time.clock() - start)
    results = cursor.fetchall()
    conn.close()
    if len(results) == 0:
        return False, False
    out = 'List of suitable flights from ' + from_city + ' to ' + to_city + ':\n\n'
    for info in results:
        out += 'Flight number: ' + info[0] + '\n' + \
            'Departure airport: ' + info[1] + '\n' + \
            'Time and date of departure: ' + fix_time(info[3]) + '\n' + \
            'Destination airport: ' + info[4] + '\n' + \
            'Time and date of arrival: ' + fix_time(info[6]) + '\n' + \
            'Average delay time (min): ' + str(fix_zero(info[7]))[:-2] + '\n\n'
    coords = (results[0][9], results[0][10], results[0][12], results[0][13])
    return out, coords

def check_destination(message):
    text = message.text
    all_cities = airport_get_all('City')
    text = " ".join(text.split())
    tokens = text.split(' ')
    text = [tokens[i].title() for i in range(len(tokens))]
    try:
        to_ind = text.index('To')
    except:
        return False
    from_city = ' '.join(text[1:to_ind]).strip()
    to_city = ' '.join(text[to_ind+1:len(text)]).strip()
    if from_city in all_cities and to_city in all_cities:
        return True
    else:
        return False

def parse_destination(text):
    all_cities = airport_get_all('City')
    text = " ".join(text.split())
    tokens = text.split(' ')
    text = [tokens[i].title() for i in range(len(tokens))]
    to_ind = text.index('To')
    from_city = ' '.join(text[1:to_ind]).strip()
    to_city = ' '.join(text[to_ind+1:len(text)]).strip()
    if from_city in all_cities and to_city in all_cities:
        return from_city, to_city
    else:
        return False

def parse_rating_score(rating, clas):
    if clas == None:
        out = 'Rating by average score\n\n'
    else:
        out = 'Rating by average score in ' + clas + ' class' + '\n\n'
    for rate in rating:
        out += 'Airline code: ' + rate[0] + '\n' + \
            'Airline name: ' + rate[1] + '\n' + \
            'Average score: ' + str(rate[2]) + '\n\n'
    return out

def parse_rating_recommend(rating, clas):
    if clas == None:
        out = 'Rating by recommendations\n\n'
    else:
        out = 'Rating by recommendations in ' + clas + ' class' + '\n\n'
    for rate in rating:
        out += 'Airline code: ' + rate[0] + '\n' + \
            'Airline name: ' + rate[1] + '\n' + \
            'Percentage of positive feedbacks: ' + str(rate[2]) + '%' + '\n\n'
    return out

def parse_rating_delay(rating):
    out = 'Rating by flight delays:' + '\n\n'
    for rate in rating:
        out += 'Airline code: ' + rate[0] + '\n' + \
            'Airline name: ' + rate[1] + '\n' + \
            'Average delay time (min): ' + str(fix_zero(rate[2]))[:-2] + '\n' + \
            'Average delay prediction (min): ' + str(fix_zero(rate[3]))[:-2] + '\n\n'
    return out

def parse_feedback(feedbacks):
    out = ''
    for feed in feedbacks:
        out += 'Feedback:\n\n'
        out += 'Airline code: ' + feed[0] + '\n' + \
            'Airline name: ' + feed[1] + '\n' + \
            'Flight number: ' + feed[2] + '\n' + \
            'Score: ' + str(feed[3]) + '\n' + \
            'Recommendation (0 or 1): ' + str(feed[4]) + '\n' + \
            'Class: ' + feed[5] + '\n' + \
            'Feedback text: ' + '\n' + feed[6] + '\n\n'

    return out

def pure_request(request):
    conn = sqlite3.connect(dbname)
    cursor = conn.cursor()
    cursor.execute(request)
    res = cursor.fetchall()
    res = set([i[0] for i in res])
    conn.close()
    return res

def airport_get_all(word):
    conn = sqlite3.connect(dbname)
    cursor = conn.cursor()
    request = 'SELECT DISTINCT ' + word + ' FROM Airports'
    cursor.execute(request)
    res = cursor.fetchall()
    res = set([i[0] for i in res])
    conn.close()
    return res

def airport_create_out(request, message):
    conn = sqlite3.connect(dbname)
    cursor = conn.cursor()

    if 'LIKE' in request:
        new_request = request + "'%" + message.text + "%'"
    else:
        new_request = request + "'" + message.text + "'"

    cursor.execute(new_request)
    results = cursor.fetchall()
    conn.close()
    out = ''
    for tup in results:
        out += 'Airport:\n\n'
        out += 'Airport code: ' + tup[0] + '\n' + \
               'Airport name: ' + tup[1] + '\n' + \
               'City: ' + tup[2] + '\n' + \
               'State: ' + tup[3] + '\n\n'

    return out

def console(call):
    #bot.send_message(13397633, message.from_user.first_name, message.from_user.id)

    print('\n~~~~~~~~~')
    print(datetime.now())
    print('Message from {}. ID: {}. Where: {}.'.format(
        call.message.chat.username, str(call.message.chat.id), call.data))

@bot.message_handler(commands=['start'])
def inline(message):
    key = types.InlineKeyboardMarkup(row_width=1)
    but_1 = types.InlineKeyboardButton(text='Airport information', callback_data='airport')
    but_2 = types.InlineKeyboardButton(text='Airline information', callback_data='airline')
    but_3 = types.InlineKeyboardButton(text='Find flight', callback_data='flight')
    but_4 = types.InlineKeyboardButton(text='Leave feedback', callback_data='feedback')
    key.add(but_1, but_2, but_3, but_4)
    bot.send_message(message.chat.id, 'What information would you like to receive?', reply_markup=key)
    print('\n~~~~~~~~~')
    print(datetime.now())
    print('Message from {} {}. ID: {}. Where: start.'.format(
        message.chat.first_name, message.chat.username, str(message.chat.id)))

@bot.message_handler(commands=['help'])
def inline(message):
    key = types.InlineKeyboardMarkup(row_width=1)
    but_1 = types.InlineKeyboardButton(text='List of aiport names', callback_data='list_name')
    but_2 = types.InlineKeyboardButton(text='List of airport codes', callback_data='list_code')
    but_3 = types.InlineKeyboardButton(text='List of airlines', callback_data='list_airline')
    but_4 = types.InlineKeyboardButton(text='List of cities', callback_data='list_city')
    but_5 = types.InlineKeyboardButton(text='List of state codes', callback_data='list_state')
    but_6 = types.InlineKeyboardButton(text='List of flight numbers', callback_data='list_flight')
    but_7 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
    key.add(but_1, but_2, but_3, but_4, but_5, but_6, but_7)
    bot.send_message(message.chat.id, 'Get list of 10 random titles', reply_markup=key)
    print('\n~~~~~~~~~')
    print(datetime.now())
    print('Message from {} {}. ID: {}. Where: help.'.format(
        message.chat.first_name, message.chat.username, str(message.chat.id)))

@bot.callback_query_handler(lambda c:True)
def inline_handler(c):

    if c.data == 'start':
        console(c)
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='Airport information', callback_data='airport')
        but_2 = types.InlineKeyboardButton(text='Airline information', callback_data='airline')
        but_3 = types.InlineKeyboardButton(text='Find flight', callback_data='flight')
        but_4 = types.InlineKeyboardButton(text='Leave feedback', callback_data='feedback')
        key.add(but_1, but_2, but_3, but_4)
        bot.send_message(c.message.chat.id, 'What information would you like to receive?', reply_markup=key)

# Airport

    if c.data == 'airport':
        console(c)
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='Airport name', callback_data='airport_name')
        but_2 = types.InlineKeyboardButton(text='Airport code', callback_data='airport_code')
        but_3 = types.InlineKeyboardButton(text='City', callback_data='airport_city')
        but_4 = types.InlineKeyboardButton(text='State code', callback_data='airport_state')
        but_5 = types.InlineKeyboardButton(text='<- Back', callback_data='start')
        key.add(but_1, but_2, but_3, but_4, but_5)
        bot.send_message(c.message.chat.id, 'Airport information', reply_markup=key)

    if c.data == 'airport_name':
        console(c)
        bot.send_message(c.message.chat.id, 'Please type airport name below\nFor example: MBS International Airport, or University Park Airport')
        res = airport_get_all('Airport_name')
        @bot.message_handler(func=lambda message: message.text in res, content_types=['text'])
        def handle_text(message):
            bot.send_chat_action(c.message.chat.id, 'typing')
            req_name = "SELECT ID_Airport, Airport_name, City, State FROM Airports WHERE Airport_name LIKE "
            out = airport_create_out(req_name, message)
            key = types.InlineKeyboardMarkup(row_width=1)
            but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
            key.add(but_1)
            try:
                bot.send_message(c.message.chat.id, out, reply_markup=key)
            except:
                bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airport_code':
        console(c)
        bot.send_message(c.message.chat.id, 'Please type airport code below\nFor example: MCI, BGM or OME')
        res = airport_get_all('ID_Airport')
        @bot.message_handler(func=lambda message: message.text in res, content_types=['text'])
        def handle_text2(message):
            bot.send_chat_action(c.message.chat.id, 'typing')
            req_code = "SELECT ID_Airport, Airport_name, City, State FROM Airports WHERE ID_Airport = "
            out = airport_create_out(req_code, message)
            key = types.InlineKeyboardMarkup(row_width=1)
            but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
            key.add(but_1)
            try:
                bot.send_message(c.message.chat.id, out, reply_markup=key)
            except:
                bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airport_city':
        console(c)
        bot.send_message(c.message.chat.id, 'Please type city name below\nFor example: New York, Las Vegas or Seattle')
        res = airport_get_all('City')
        @bot.message_handler(func=lambda message: message.text in res, content_types=['text'])
        def handle_text3(message):
            bot.send_chat_action(c.message.chat.id, 'typing')
            req_city = "SELECT ID_Airport, Airport_name, City, State FROM Airports WHERE City LIKE "
            out = airport_create_out(req_city, message)
            key = types.InlineKeyboardMarkup(row_width=1)
            but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
            key.add(but_1)
            try:
                bot.send_message(c.message.chat.id, out, reply_markup=key)
            except:
                bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airport_state':
        console(c)
        res = airport_get_all('State')
        bot.send_message(c.message.chat.id, 'Please type state abbreviation below\nFor example: TX, MO or NV')
        @bot.message_handler(func=lambda message: message.text in res, content_types=['text'])
        def handle_text4(message):
            bot.send_chat_action(c.message.chat.id, 'typing')
            req_state = "SELECT ID_Airport, Airport_name, City, State FROM Airports WHERE State = "
            out = airport_create_out(req_state, message)
            key = types.InlineKeyboardMarkup(row_width=1)
            but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
            key.add(but_1)
            try:
                bot.send_message(c.message.chat.id, out, reply_markup=key)
            except:
                bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

# Airline

    if c.data == 'airline':
        console(c)
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='Airline ratings', callback_data='airline_rating')
        but_2 = types.InlineKeyboardButton(text='Airline feedbacks', callback_data='airline_feedback')
        but_3 = types.InlineKeyboardButton(text='<- Back', callback_data='start')
        key.add(but_1, but_2, but_3)
        bot.send_message(c.message.chat.id, 'Airline information', reply_markup=key)

    if c.data == 'airline_rating':
        console(c)
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='By class (Business / Economy)', callback_data='airline_rating_class')
        but_2 = types.InlineKeyboardButton(text='By time', callback_data='airline_rating_time')
        but_3 = types.InlineKeyboardButton(text='By flight delays', callback_data='airline_rating_delay')
        but_4 = types.InlineKeyboardButton(text='<- Back', callback_data='airline')
        but_5 = types.InlineKeyboardButton(text='<<-- Main menu ', callback_data='start')
        key.add(but_1, but_2, but_3, but_4, but_5)
        bot.send_message(c.message.chat.id, 'Airline ratings', reply_markup=key)

    if c.data == 'airline_rating_class':
        console(c)
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='Business class', callback_data='airline_rating_class_business')
        but_2 = types.InlineKeyboardButton(text='Economy class', callback_data='airline_rating_class_econom')
        but_3 = types.InlineKeyboardButton(text='<- Back', callback_data='airline_rating')
        but_4 = types.InlineKeyboardButton(text='<<-- Main page', callback_data='start')
        key.add(but_1, but_2, but_3, but_4)
        bot.send_message(c.message.chat.id, 'Airline rating by class', reply_markup=key)

    if c.data == 'airline_rating_class_business':
        console(c)
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text="Based on users' recommendations", callback_data='airline_rating_class_business_recommend')
        but_2 = types.InlineKeyboardButton(text="Based on users' evaluation", callback_data='airline_rating_class_business_score')
        but_3 = types.InlineKeyboardButton(text='<- Back', callback_data='airline_rating_class')
        but_4 = types.InlineKeyboardButton(text='<<-- Main page', callback_data='start')
        key.add(but_1, but_2, but_3, but_4)
        bot.send_message(c.message.chat.id, 'Airline rating by business class', reply_markup=key)

    if c.data == 'airline_rating_class_econom':
        console(c)
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text="Based on users' recommendations", callback_data='airline_rating_class_econom_recommend')
        but_2 = types.InlineKeyboardButton(text="Based on users' evaluation", callback_data='airline_rating_class_econom_score')
        but_3 = types.InlineKeyboardButton(text='<- Back', callback_data='airline_rating_class')
        but_4 = types.InlineKeyboardButton(text='<<-- Main page', callback_data='start')
        key.add(but_1, but_2, but_3, but_4)
        bot.send_message(c.message.chat.id, 'Рейтинг авиакомпаний по Эконом-классу', reply_markup=key)

    if c.data == 'airline_rating_class_business_recommend':
        console(c)
        bot.send_chat_action(c.message.chat.id, 'typing')
        conn = sqlite3.connect(dbname)
        cursor = conn.cursor()
        new_request = '''SELECT a.ID_Airline, Airline_name, ROUND(AVG(Cast(Recommendation as Float)) * 100, 1) As Satisfaction_level FROM Airlines AS a \
                      INNER JOIN Feedbacks AS f ON a.ID_Airline = f.ID_Airline WHERE Class LIKE '%Class' GROUP BY a.ID_Airline ORDER BY Satisfaction_level DESC'''
        cursor.execute(new_request)
        results = cursor.fetchall()
        out = parse_rating_recommend(results, 'Business')
        conn.close()
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
        key.add(but_1)
        try:
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airline_rating_class_business_score':
        console(c)
        bot.send_chat_action(c.message.chat.id, 'typing')
        conn = sqlite3.connect(dbname)
        cursor = conn.cursor()
        new_request = '''SELECT a.ID_Airline, Airline_name, ROUND(AVG(Cast(Score as Float)), 2) As Rating FROM Airlines AS a \
                      INNER JOIN Feedbacks AS f ON a.ID_Airline = f.ID_Airline WHERE Class LIKE '%Class' GROUP BY a.ID_Airline ORDER BY Rating DESC'''
        cursor.execute(new_request)
        results = cursor.fetchall()
        out = parse_rating_score(results, 'Business')
        conn.close()
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
        key.add(but_1)
        try:
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airline_rating_class_econom_recommend':
        console(c)
        bot.send_chat_action(c.message.chat.id, 'typing')
        conn = sqlite3.connect(dbname)
        cursor = conn.cursor()
        new_request = '''SELECT a.ID_Airline, Airline_name, ROUND(AVG(Cast(Recommendation as Float)) * 100, 1) As Satisfaction_level FROM Airlines AS a \
                      INNER JOIN Feedbacks AS f ON a.ID_Airline = f.ID_Airline WHERE Class LIKE '%Economy' GROUP BY a.ID_Airline ORDER BY Satisfaction_level DESC'''
        cursor.execute(new_request)
        results = cursor.fetchall()
        out = parse_rating_recommend(results, 'Economy')
        conn.close()
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
        key.add(but_1)
        try:
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airline_rating_class_econom_score':
        console(c)
        bot.send_chat_action(c.message.chat.id, 'typing')
        conn = sqlite3.connect(dbname)
        cursor = conn.cursor()
        new_request = '''SELECT a.ID_Airline, Airline_name, ROUND(AVG(Cast(Score as Float)), 2) As Rating FROM Airlines AS a \
                      INNER JOIN Feedbacks AS f ON a.ID_Airline = f.ID_Airline WHERE Class LIKE '%Economy' GROUP BY a.ID_Airline ORDER BY Rating DESC'''
        cursor.execute(new_request)
        results = cursor.fetchall()
        out = parse_rating_score(results, 'Economy')
        conn.close()
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
        key.add(but_1)
        try:
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airline_rating_time':
        console(c)
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='For the last week', callback_data='airline_rating_time_week')
        but_2 = types.InlineKeyboardButton(text='For the last month', callback_data='airline_rating_time_month')
        but_3 = types.InlineKeyboardButton(text='For the last 2 months', callback_data='airline_rating_time_month2')
        but_4 = types.InlineKeyboardButton(text='<- Back', callback_data='airline_rating')
        but_5 = types.InlineKeyboardButton(text='<<-- Main page', callback_data='start')
        key.add(but_1, but_2, but_3, but_4, but_5)
        bot.send_message(c.message.chat.id, 'Airline rating by time', reply_markup=key)

    if c.data == 'airline_rating_time_week':
        console(c)
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text="Based on users' recommendations", callback_data='airline_rating_time_week_recommend')
        but_2 = types.InlineKeyboardButton(text="Based on users' evaluation", callback_data='airline_rating_time_week_score')
        but_3 = types.InlineKeyboardButton(text='<- Back', callback_data='airline_rating_time')
        but_4 = types.InlineKeyboardButton(text='<<-- Main page', callback_data='start')
        key.add(but_1, but_2, but_3, but_4)
        bot.send_message(c.message.chat.id, 'Airline rating for the last week', reply_markup=key)

    if c.data == 'airline_rating_time_week_recommend':
        console(c)
        bot.send_chat_action(c.message.chat.id, 'typing')
        conn = sqlite3.connect(dbname)
        cursor = conn.cursor()
        new_request = '''SELECT a.ID_Airline, Airline_name, ROUND(AVG(Cast(Recommendation as Float)) * 100, 1) As Satisfaction_level FROM Airlines AS a \
                      INNER JOIN Feedbacks AS f ON a.ID_Airline = f.ID_Airline WHERE date(f.Date, '+7 day') > (SELECT MAX(Date) FROM Feedbacks) GROUP BY a.ID_Airline \
                      ORDER BY Satisfaction_level DESC'''
        cursor.execute(new_request)
        results = cursor.fetchall()
        out = parse_rating_recommend(results, None)
        conn.close()
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
        key.add(but_1)
        try:
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airline_rating_time_week_score':
        console(c)
        bot.send_chat_action(c.message.chat.id, 'typing')
        conn = sqlite3.connect(dbname)
        cursor = conn.cursor()
        new_request = '''SELECT a.ID_Airline, Airline_name, ROUND(AVG(Cast(Score as Float)), 1) As Rating FROM Airlines AS a INNER JOIN Feedbacks AS f \
                      ON a.ID_Airline = f.ID_Airline WHERE date(f.Date, '+7 day') > (SELECT MAX(Date) FROM Feedbacks) GROUP BY a.ID_Airline ORDER BY Rating DESC'''
        cursor.execute(new_request)
        results = cursor.fetchall()
        out = parse_rating_score(results, None)
        conn.close()
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
        key.add(but_1)
        try:
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airline_rating_time_month':
        console(c)
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text="Based on users' recommendations", callback_data='airline_rating_time_month_recommend')
        but_2 = types.InlineKeyboardButton(text="Based on users' evaluation", callback_data='airline_rating_time_month_score')
        but_3 = types.InlineKeyboardButton(text='<- Back', callback_data='airline_rating_time')
        but_4 = types.InlineKeyboardButton(text='<<-- Main page', callback_data='start')
        key.add(but_1, but_2, but_3, but_4)
        bot.send_message(c.message.chat.id, 'Airline rating for the last month', reply_markup=key)

    if c.data == 'airline_rating_time_month_recommend':
        console(c)
        bot.send_chat_action(c.message.chat.id, 'typing')
        conn = sqlite3.connect(dbname)
        cursor = conn.cursor()
        new_request = '''SELECT a.ID_Airline, Airline_name, ROUND(AVG(Cast(Recommendation as Float)) * 100, 1) As Satisfaction_level FROM Airlines AS a \
                      INNER JOIN Feedbacks AS f ON a.ID_Airline = f.ID_Airline WHERE date(f.Date, '+1 month') > (SELECT MAX(Date) FROM Feedbacks) GROUP BY a.ID_Airline \
                      ORDER BY Satisfaction_level DESC'''
        cursor.execute(new_request)
        results = cursor.fetchall()
        out = parse_rating_recommend(results, None)
        conn.close()
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
        key.add(but_1)
        try:
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airline_rating_time_month_score':
        console(c)
        bot.send_chat_action(c.message.chat.id, 'typing')
        conn = sqlite3.connect(dbname)
        cursor = conn.cursor()
        new_request = '''SELECT a.ID_Airline, Airline_name, ROUND(AVG(Cast(Score as Float)), 1) As Rating FROM Airlines AS a INNER JOIN Feedbacks AS f \
                      ON a.ID_Airline = f.ID_Airline WHERE date(f.Date, '+1 month') > (SELECT MIN(Date) FROM Feedbacks) GROUP BY a.ID_Airline ORDER BY Rating DESC'''
        cursor.execute(new_request)
        results = cursor.fetchall()
        out = parse_rating_score(results, None)
        conn.close()
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
        key.add(but_1)
        try:
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airline_rating_time_month2':
        console(c)
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text="Based on users' recommendations", callback_data='airline_rating_time_month2_recommend')
        but_2 = types.InlineKeyboardButton(text="Based on users' evaluation", callback_data='airline_rating_time_month2_score')
        but_3 = types.InlineKeyboardButton(text='<- Back', callback_data='airline_rating_time')
        but_4 = types.InlineKeyboardButton(text='<<-- Main page', callback_data='start')
        key.add(but_1, but_2, but_3, but_4)
        bot.send_message(c.message.chat.id, 'Airline rating for the last 2 months', reply_markup=key)

    if c.data == 'airline_rating_time_month2_recommend':
        console(c)
        bot.send_chat_action(c.message.chat.id, 'typing')
        conn = sqlite3.connect(dbname)
        cursor = conn.cursor()
        new_request = '''SELECT a.ID_Airline, Airline_name, ROUND(AVG(Cast(Recommendation as Float)) * 100, 1) As Satisfaction_level FROM Airlines AS a \
                      INNER JOIN Feedbacks AS f ON a.ID_Airline = f.ID_Airline WHERE date(f.Date, '+2 months') > (SELECT MAX(Date) FROM Feedbacks) GROUP BY a.ID_Airline \
                      ORDER BY Satisfaction_level DESC'''
        cursor.execute(new_request)
        results = cursor.fetchall()
        out = parse_rating_recommend(results, None)
        conn.close()
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
        key.add(but_1)
        try:
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airline_rating_time_month2_score':
        console(c)
        bot.send_chat_action(c.message.chat.id, 'typing')
        conn = sqlite3.connect(dbname)
        cursor = conn.cursor()
        new_request = '''SELECT a.ID_Airline, Airline_name, ROUND(AVG(Cast(Score as Float)), 1) As Rating FROM Airlines AS a INNER JOIN Feedbacks AS f \
                      ON a.ID_Airline = f.ID_Airline WHERE date(f.Date, '+2 month') > (SELECT MAX(Date) FROM Feedbacks) GROUP BY a.ID_Airline ORDER BY Rating DESC'''
        cursor.execute(new_request)
        results = cursor.fetchall()
        out = parse_rating_score(results, None)
        conn.close()
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
        key.add(but_1)
        try:
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airline_rating_delay':
        console(c)
        bot.send_chat_action(c.message.chat.id, 'typing')
        conn = sqlite3.connect(dbname)
        cursor = conn.cursor()
        new_request = '''SELECT DISTINCT q.Airline_code, Airline_name, q.Avg_delay, q.Avg_prediction FROM (SELECT f.ID_Flight, \
        substr(f.ID_Flight, 1, 2) AS Airline_code, ROUND(AVG(JulianDay(ar.Actual_arrival) - JulianDay(ar.Scheduled_arrival)) * 24 * 60) AS \
        Avg_delay, ROUND(AVG(Delay_prediction)) AS Avg_prediction FROM Flights AS f INNER JOIN Flights_Airports_ar AS ar ON f.ID_Flight = ar.ID_Flight
        WHERE time(ar.Actual_arrival) != '00:00:00' AND (time(ar.Actual_arrival) - time(ar.Scheduled_arrival)) BETWEEN -12 AND 12 \
        GROUP BY substr(f.ID_Flight, 1, 2) HAVING Avg_delay <= 10) AS q INNER JOIN Airplanes_Flights AS af ON q.ID_Flight = af.ID_Flight \
        INNER JOIN Airplanes AS p ON af.ID_Airplane = p.ID_Airplane INNER JOIN Airlines AS l ON p.ID_Airline = l.ID_Airline ORDER BY q.Avg_delay'''
        cursor.execute(new_request)
        results = cursor.fetchall()
        out = parse_rating_delay(results)
        conn.close()
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
        key.add(but_1)
        try:
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'airline_feedback':
        console(c)
        bot.send_message(c.message.chat.id, 'Please type airline code below\nFor example: AA, HA or DL')
        res = pure_request('SELECT DISTINCT ID_Airline FROM Airlines')
        @bot.message_handler(func=lambda message: message.text in res, content_types=['text'])
        def handle_text(message):
            bot.send_chat_action(c.message.chat.id, 'typing')
            conn = sqlite3.connect(dbname)
            cursor = conn.cursor()
            new_request = '''SELECT a.ID_Airline, Airline_name, ID_Flight, score, recommendation, class, content \
                            FROM Airlines AS a INNER JOIN Feedbacks AS f ON a.ID_Airline = f.ID_Airline WHERE a.ID_Airline = ''' + \
                            "'" + message.text + "'" + '''ORDER BY random() LIMIT 2'''
            cursor.execute(new_request)
            results = cursor.fetchall()
            out = parse_feedback(results)
            conn.close()
            key = types.InlineKeyboardMarkup(row_width=1)
            but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
            key.add(but_1)
            try:
                bot.send_message(c.message.chat.id, out, reply_markup=key)
            except:
                bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

# Flight

    if c.data == 'flight':
        console(c)
        key = types.InlineKeyboardMarkup(row_width=1)
        but_1 = types.InlineKeyboardButton(text='By flight number', callback_data='flight_number')
        but_2 = types.InlineKeyboardButton(text='By airline', callback_data='flight_airline')
        but_3 = types.InlineKeyboardButton(text='By departure and destination cities', callback_data='flight_places')
        but_4 = types.InlineKeyboardButton(text='<- Back', callback_data='start')
        key.add(but_1, but_2, but_3, but_4)
        bot.send_message(c.message.chat.id, 'Find flight', reply_markup=key)

    if c.data == 'flight_number':
        console(c)
        bot.send_message(c.message.chat.id, 'Please type flight number in the following format:\nFlight <flight_number>\nFor example: Flight B626 or Flight DL1835')
        @bot.message_handler(func=check_flight, content_types=['text'])
        def handle_text3(message):
            bot.send_chat_action(c.message.chat.id, 'typing')
            out = request_flight(message.text.split(' ')[-1].upper())
            if not out:
                bot.send_message(c.message.chat.id, 'Wrong flight number')
            else:
                key = types.InlineKeyboardMarkup(row_width=1)
                but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
                key.add(but_1)
                try:
                    bot.send_message(c.message.chat.id, out, reply_markup=key)
                except:
                    bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'flight_airline':
        console(c)
        bot.send_message(c.message.chat.id, 'Please type airline code in the following format:\nAirline <flight_number>\nFor example: Airline AA or Airline UA')
        @bot.message_handler(func=check_airline, content_types=['text'])
        def handle_text(message):
            bot.send_chat_action(c.message.chat.id, 'typing')
            cur_airline = check_airline(message)
            out = request_airline(cur_airline)
            if not out:
                bot.send_message(c.message.chat.id, 'No information about this airline')
            else:
                key = types.InlineKeyboardMarkup(row_width=1)
                but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
                key.add(but_1)
                try:
                    bot.send_message(c.message.chat.id, out, reply_markup=key)
                except:
                    bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'flight_places':
        console(c)
        bot.send_message(c.message.chat.id, 'Please type departure and destination cities in the following format:\nFrom <city_name> to <city_name>\nFor example: From New York to Seattle')
        @bot.message_handler(func=check_destination, content_types=['text'])
        def handle_text3(message):
            bot.send_chat_action(c.message.chat.id, 'typing')
            from_city, to_city = parse_destination(message.text)
            new_request = """SELECT DISTINCT t.*, ROUND(Delay_Prediction) AS Delay_Prediction, a1.City AS City1, a1.Longitude \
            AS long1, a1.Latitude AS lat1, a2.City AS City2, a2.Longitude AS long2, a2.Latitude AS lat2 FROM (SELECT dep.ID_flight, dep.ID_Airport \
            AS Airport_dep, dep.Actual_departure, dep.Scheduled_departure, ar.ID_Airport AS Airport_ar, ar.Actual_arrival, ar.Scheduled_arrival \
            FROM Flights_Airports_dep AS dep INNER JOIN Flights_Airports_ar AS ar ON dep.rowid = ar.rowid) AS t INNER JOIN Flights AS f ON f.ID_Flight = t.ID_Flight \
            INNER JOIN Airports AS a1 ON a1.ID_Airport = t.Airport_dep INNER JOIN Airports AS a2 ON a2.ID_Airport = t.Airport_ar \
            WHERE a1.City = ? AND a2.City = ? ORDER BY t.Scheduled_departure DESC LIMIT 5"""
            new_request = new_request.replace('a1.City = ?', 'a1.City = ' + "'" + from_city + "'")
            new_request = new_request.replace('a2.City = ?', 'a2.City = ' + "'" + to_city + "'")
            out, coords = request_destinations(new_request, from_city, to_city, c)
            if not out and not coords:
                bot.send_message(c.message.chat.id, 'No flights available')
            else:
                key = types.InlineKeyboardMarkup(row_width=1)
                but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
                key.add(but_1)
                try:
                    bot.send_chat_action(c.message.chat.id, 'upload_photo')
                    map_name = get_beautiful_map(coords, from_city, to_city)
                    map = open(map_name, 'rb')
                    bot.send_message(c.message.chat.id, out)
                    bot.send_message(c.message.chat.id, 'Here is your trip:')
                    bot.send_photo(c.message.chat.id, map, reply_markup=key)
                except:
                    bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'list_name':
        console(c)
        try:
            names = airport_get_all('Airport_name')
            chosen = random.choices(list(names), k=10)
            header = 'List of airport names:'
            out = prepare_list(header, chosen)
            key = types.InlineKeyboardMarkup(row_width=1)
            but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
            key.add(but_1)
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'list_code':
        console(c)
        try:
            names = airport_get_all('ID_Airport')
            chosen = random.choices(list(names), k=10)
            header = 'List of airport codes:'
            out = prepare_list(header, chosen)
            key = types.InlineKeyboardMarkup(row_width=1)
            but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
            key.add(but_1)
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'list_airline':
        console(c)
        try:
            results = get_airlines()
            out = 'List of airline codes and names:\n\n'
            for info in results:
                out += info[0] + ' ' + info[1] + '\n'
            key = types.InlineKeyboardMarkup(row_width=1)
            but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
            key.add(but_1)
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'list_city':
        console(c)
        try:
            names = airport_get_all('City')
            chosen = random.choices(list(names), k=10)
            header = 'List of cities:'
            out = prepare_list(header, chosen)
            key = types.InlineKeyboardMarkup(row_width=1)
            but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
            key.add(but_1)
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'list_state':
        console(c)
        try:
            names = airport_get_all('State')
            chosen = random.choices(list(names), k=10)
            header = 'List of state codes:'
            out = prepare_list(header, chosen)
            key = types.InlineKeyboardMarkup(row_width=1)
            but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
            key.add(but_1)
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'list_flight':
        console(c)
        try:
            names = get_flights()
            chosen = random.choices(list(names), k=10)
            header = 'List of flight numbers:'
            out = prepare_list(header, chosen)
            key = types.InlineKeyboardMarkup(row_width=1)
            but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
            key.add(but_1)
            bot.send_message(c.message.chat.id, out, reply_markup=key)
        except:
            bot.send_message(c.message.chat.id, 'Something went wrong :(', reply_markup=key)

    if c.data == 'feedback':
        console(c)
        bot.send_message(c.message.chat.id, 'Please type your name in the following format:\nName <your_name>\nFor example: Name Petr Petrov')
        @bot.message_handler(func=check_feedback_name, content_types=['text'])
        def handle_text(message):
            name = message.text.strip()
            name = name.split(' ')[1:]
            name = ' '.join(name)
            bot.send_message(c.message.chat.id, 'Please type your country in the following format:\nCountry <country_name>\nFor example: Country Russia')
            @bot.message_handler(func=check_feedback_country, content_types=['text'])
            def handle_text(message):
                country = message.text.split(' ')[-1].title()
                author = name.title()
                bot.send_message(c.message.chat.id, 'Please type airline code and flight number in the following format:\n\
Airline <airline_code> flight <flight_number>\nFor example: Airline UA flight UA420')
                @bot.message_handler(func=check_feedback_airline_flight, content_types=['text'])
                def handle_text(message):
                    tokens = message.text.split(' ')
                    airline, flight = tokens[1], tokens[3]
                    bot.send_message(c.message.chat.id, 'Please type the date of your trip in following format:\nDate <date>\nFor example: Date 2000-01-01')
                    @bot.message_handler(func=check_feedback_date, content_types=['text'])
                    def handle_text(message):
                        tokens = message.text.split(' ')
                        date = tokens[-1]
                        bot.send_message(c.message.chat.id, 'Please type your class (business or economy), evaluation (integer from 0 to 10)\n\
and recommendation (yes or no) in following format:\n<class> <evaluation> <recommendation>\nFor example: Business 9 YES')
                        @bot.message_handler(func=check_feedback_class, content_types=['text'])
                        def handle_text(message):
                            text = message.text
                            tokens = text.split(' ')
                            clas, score, recommendation = tokens[0].title(), str(tokens[1]), tokens[2]
                            recommendation = '1' if recommendation == 'YES' else '0'
                            bot.send_message(c.message.chat.id, 'Please leave your feedback here in following format:\nFeedback <your_feedback>\nFor example: Feedback Everything is OK!')
                            @bot.message_handler(func=check_feedback_content, content_types=['text'])
                            def handle_text(message):
                                text = message.text.split(' ')
                                feedback = ' '.join(text[1:])
                                requests = []
                                requests.append('BEGIN TRANSACTION;')
                                requests.append('INSERT INTO Authors (ID_Author, Country) VALUES (' + "'" + author + "'" + ', ' + "'" + country + "'" + ') ')
                                requests.append('INSERT INTO Feedbacks (ID_Airline, ID_Author, ID_Flight, DATE, Score, Recommendation, Class, Content) VALUES (' + \
                                "'" + airline + "'" + ', ' + "'" + author + "'" + ', ' + "'" + flight + "'" + ', ' + "'" + date + "'" + ', ' + "'" + score + "'" + \
                                ', ' + "'" + recommendation + "'" + ', ' + "'" + clas + "'" + ', ' + "'" + feedback + "'" + ') ')
                                requests.append('COMMIT;')
                                conn = sqlite3.connect(dbname)
                                cursor = conn.cursor()
                                for req in requests:
                                    cursor.execute(req)
                                conn.close()
                                key = types.InlineKeyboardMarkup(row_width=1)
                                but_1 = types.InlineKeyboardButton(text='<<-- Main menu', callback_data='start')
                                key.add(but_1)
                                bot.send_message(c.message.chat.id, 'Your feedback was added! Thank you!', reply_markup=key)
                                console(c)

bot.polling(none_stop=True)