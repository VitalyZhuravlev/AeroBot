# AeroBot

As a part of "Database Theory" course our team has created a [Telegram Bot](https://core.telegram.org/bots) that provides information about American airports, airlines and its flights.

## Data

We used datasets from Kaggle competition and GitHub:

[Dataset 1](https://www.kaggle.com/usdot/flight-delays)

[Dataset 2](https://github.com/quankiquanki/skytrax-reviews-dataset/tree/master/data)

First dataset contains information about completed flights of American airlines for 2015 year. Second dataset provides feedbacks on these airlines.

## Relational database

After processing datasets we defined six entities and their attributes that are the foundation of our database:

- Airport (ID, full name, city, state, coordinates)
- Aircraft (ID)
- Airline (ID, name, country)
- Flight (number, predicted delay)
- Feedback (ID, date, content, class, score and recommendation)
- Feedbacks' author (nickname, country)

There are connections between these entities. For example, author has got a feedback on an airline, so that author and feedback are connected directly. Each airline has got aircrafts, each aircraft belongs to a certain flight, so all three entities are consistently connected with each other. Fights and airports are connected with two connections because each flight has departure and destination airports.

After we identified connections we created ER and TR diagrams in order to clearly show all relations between entities:

ER diagram:

![ER](https://i.ibb.co/XDh6KMQ/photo-2018-12-16-02-19-09.jpg)

TR diagram:

![TR](https://i.ibb.co/2NhG23k/photo-2018-12-16-23-25-19.jpg)

Then based on diagrams we created a SQL relational database.

## Client application

The client application represents a Telegram Bot that is hosted on a local server and is sending requests to a local SQL database. 

After opening the Bot user can start using Bot by typing `/start` or get help by typing `/help`. These menus can be called anytime. When typing `/help` user gets lists of airport names, airport codes, airline names, etc.:

![Help](https://i.ibb.co/85jjWzy/1.png)

When typing `/start` user is offered options: get information about airport, airline, find flight or leave a feedback on airline:

![Start](https://i.ibb.co/hdyHWtk/1.png)

#### Airport information

When user clicks the airport information button user can obtain information about airport by name, code or show the list of airports in certain city or state. That is how the information about Seattle airports looks:

![Airport](https://i.ibb.co/12H5rhY/1.png)

#### Airline information

After clicking airline information button user can obtain airline rating by class (Business or Economy), by time (last week, month or 2 months) or flight delays:

![Airlines](https://i.ibb.co/PQW8bKr/1.png)

Also user can get feedbacks of airline. Ratings are based on user scores (from 0 to 10) and on recommendations (0 or 1). For example, that is how a feedback on United Airlines looks:

![United](https://i.ibb.co/cXzRhGG/1.png)



Here is the rating of airlines based on user scores flying economy class:

![Rating](https://i.ibb.co/HdtZk1K/1.png)

#### Find flight

Pressing the third button in the main menu Bot offers user to find flight by number, airline or departure and destination cities:

![Flight](https://i.ibb.co/93vnKnJ/1.png)

If user chooses to find flight by number Bot shows information about this flight: departure / destination time, airport, city; delay prediction (in minutes), feedback about this flight, score and recommendation. Here is the example:

![Info](https://i.ibb.co/YdL2ZwW/1.png)

If user chooses to find flight by destination and departure cities Bot will show the list of suitable flights and flight route map:

![1](https://i.ibb.co/s2TqCSy/1.png)

![2](https://i.ibb.co/ctJQdhQ/1.png)

#### Leave a feedback

When pressing leave a feedback button user is offered to write some information of himself and then write a feedback. That is how it looks:

![3](https://i.ibb.co/5Gswt6p/1.png)

![4](https://i.ibb.co/nb2fj2F/1.png)

## Bot realization

To create the Bot we used Python 3.6.3 and the following libraries:

- sqlite3 3.14.2	
- pyTelegramBotAPI 3.6.6	
- telebot 0.0.3	
- numpy 1.15.2	
- matplotlib 2.1.0	
- basemap 1.2.0

In order to create Bot we had to get unique key - token. Each interaction with Bot is made using this token. The whole control and interaction with bot proceeds using `pyTelegramBotAPI` and `telebot` libraries. Using `sqlite3` library we can connect to our database and send requests to it.

Each button represents itself an `Inline` button with unique `callback` identifier. Pressing the specified button activates and is being processed only this button's `callback` identifier. For example when pressing *Airport name* button in the main menu, a `callback` *airport_name* is activated and a message to the user is sent.

Any message that user sends to the Bot is processed by the first `handler`. But each `handler` can be binded to a function, so `handler` processes message only if the function takes *True* value. For example, if user sends an airport name, Bot checks whether entered name is in the list of all airport names and interacts accordingly. Also, no matter how user writes messages - in lowercase or uppercase letters.

According to buttons pressed and user's message sent, a SQL request is being formed as a string which subsequently is served as input to `execute` method of `sqlite3` library. The list that this method returns is being parsed by corresponding function and is showed to user as a bot message.

The delay predictions were received in the following way. For each unique flight differences between actual time and scheduled time were counted. Then, for each flight using *n* differences was trained a linear regression (*n* is the number of flight count). After that the delay time of *n+1*-th flight is predicted.

## SQL requests

Here are some examples of SQL requests to our database:

1. Airline rating based on users' scores for the last month:

   `SELECT a.ID_Airline, Airline_name, ROUND(AVG(Cast(Score as Float)), 1) As Rating FROM Airlines AS a INNER JOIN Feedbacks AS f ON a.ID_Airline = f.ID_Airline WHERE date(f.Date, '+1 month') > (SELECT MIN(Date) FROM Feedbacks) GROUP BY a.ID_Airline ORDER BY Rating DESC`

2. Information about flights of airline with **AA** code:

   `SELECT DISTINCT t.ID_flight, t.Airport_dep, t.Airport_ar, ROUND(Delay_Prediction) AS Delay_Prediction,     a1.City AS City1, t.Scheduled_departure, a2.City AS City2, t.Scheduled_arrivalFROM (    SELECT dep.ID_flight, dep.ID_Airport AS Airport_dep, dep.Actual_departure, dep.Scheduled_departure,         ar.ID_Airport AS Airport_ar, ar.Actual_arrival, ar.Scheduled_arrival    FROM Flights_Airports_dep AS dep    INNER JOIN Flights_Airports_ar AS ar ON dep.rowid = ar.rowid) AS tINNER JOIN Flights AS f ON f.ID_Flight = t.ID_FlightINNER JOIN Airports AS a1 ON a1.ID_Airport = t.Airport_depINNER JOIN Airports AS a2 ON a2.ID_Airport = t.Airport_arWHERE f.ID_flight LIKE ‘AA%’GROUP BY f.ID_flightHAVING Delay_prediction <= 0ORDER BY t.Scheduled_departure DESCLIMIT 5`

3. Information about **B626** flight:

   `SELECT DISTINCT t.\*, ROUND(Delay_Prediction) AS Delay_Prediction, a1.City AS City1, a2.City AS City2,ID_Author, Date, Score, Recommendation, Class, Content FROM (    SELECT dep.ID_flight, dep.ID_Airport AS Airport_dep, dep.Scheduled_departure,         ar.ID_Airport AS Airport_ar, ar.Scheduled_arrival    FROM Flights_Airports_dep AS dep    INNER JOIN Flights_Airports_ar AS ar ON dep.rowid = ar.rowid) AS tINNER JOIN Flights AS f ON f.ID_Flight = t.ID_FlightINNER JOIN Airports AS a1 ON a1.ID_Airport = t.Airport_depINNER JOIN Airports AS a2 ON a2.ID_Airport = t.Airport_arLEFT JOIN Feedbacks AS r ON f.ID_Flight = r.ID_FlightWHERE t.ID_flight = ‘B626’GROUP BY t.Scheduled_departureORDER BY t.Scheduled_departure DESCLIMIT 1`

4. List of flights from Denver to New York:

   `SELECT DISTINCT t.\*, ROUND(Delay_Prediction) AS Delay_Prediction, a1.City AS City1, a1.Longitude AS long1, a1.Latitude AS lat1, a2.City AS City2, a2.Longitude AS long2, a2.Latitude AS lat2FROM (    SELECT dep.ID_flight, dep.ID_Airport AS Airport_dep, dep.Actual_departure, dep.Scheduled_departure,         ar.ID_Airport AS Airport_ar, ar.Actual_arrival, ar.Scheduled_arrival    FROM Flights_Airports_dep AS dep    INNER JOIN Flights_Airports_ar AS ar ON dep.rowid = ar.rowid) AS tINNER JOIN Flights AS f ON f.ID_Flight = t.ID_FlightINNER JOIN Airports AS a1 ON a1.ID_Airport = t.Airport_depINNER JOIN Airports AS a2 ON a2.ID_Airport = t.Airport_arWHERE a1.City = ‘Denver’ AND a2.City = ‘New York’ORDER BY t.Scheduled_departure DESCLIMIT 5`

5. Airline rating by flight delays:

   `SELECT DISTINCT q.Airline_code, Airline_name, q.Avg_delay, q.Avg_predictionFROM (    SELECT f.ID_Flight, substr(f.ID_Flight, 1, 2) AS Airline_code,         ROUND(AVG(JulianDay(ar.Actual_arrival) - JulianDay(ar.Scheduled_arrival)) \* 24 * 60) AS Avg_delay,        ROUND(AVG(Delay_prediction)) AS Avg_prediction    FROM Flights AS f    INNER JOIN Flights_Airports_ar AS ar ON f.ID_Flight = ar.ID_Flight    WHERE time(ar.Actual_arrival) != '00:00:00' AND (time(ar.Actual_arrival) - time(ar.Scheduled_arrival)) BETWEEN -12 AND 12    GROUP BY substr(f.ID_Flight, 1, 2)    HAVING Avg_delay <= 10) AS qINNER JOIN Airplanes_Flights AS af ON q.ID_Flight = af.ID_FlightINNER JOIN Airplanes AS p ON af.ID_Airplane = p.ID_AirplaneINNER JOIN Airlines AS l ON p.ID_Airline = l.ID_AirlineORDER BY q.Avg_delay`

   ​

   ## Links

   Here is the link to AeroBot: [Link](https://t.me/aero_flight_bot)

   ## Our team

   - Pugachev Alexander
   - Torop Viktoria
   - Mugtasimov Daniil
   - Juravlev Vitaly