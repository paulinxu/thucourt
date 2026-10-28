
# THUCourt

This is a website we are trying to develop. It is a platform that will be used for students inside Tsinghua University.

Ideally, students should be able to log in using WeChat, and then verify themselves by introducing their real name and student id. 


# Sections:

**grid view note:**

There are two court areas: zijing and beiguan. zijing has 14 courts. beiguan has 4 courts. The available dates are always 4: the current date and three dates into the future. The user can switch between the two court areas and 4 dates. The avalible time slots per date are as follows: 8am to 10pm (1h slots) (time slot durations might be subject to change later). So for any chosen date, zijing area grid should be 14 columns and 14 rows, while beiguan area grid should be 4 columns and 14 rows. 

**deletion note:**

All created requests can be deleted by the user that created them.

## Buy and sell

- Two available views: list or grid
- Sell offer list shows sell offers from all users. It contains a filtering tool (can choose time, court area, date). 
- Buy offer list shows buy offers from all users. It contains a filtering tool (can choose time, court area, date). 
- Grid mode shows the number of buy offers and sell offers on each available time slot. See the grid view note.

- By pressing on a slot, the user can choose to create a buy or sell offer or to contact a user who has already created a buy or sell offer. 

- zijing courts are 15 rmb per slot. beiguan courts are 120 rmb per slot.

## Trade

- Create trade offer using a button
- List view shows sell offers from other users in a list. It contains a filtering tool (can choose time, court area, date). 

## Find games

- Two available views: list or grid
- List view shows find game requests. It contains a filtering tool (can choose time, court area, date, player level). 
- Grid mode shows find game requests on each time slot. See the grid view note. Note: grids should contain one column only. They should put all the game requests at one time slice together. 

- By pressing on a slot, the user can choose to create a find game request or to contact a user who has already created such a request. 

## Record official match score

Players decide beforehand that they will play a match that will be scored here. After playing, they record the results here. 

When submitting results:
- Select oponent
- Write game scores
- Select the winner or draw
- Select the date played

The opponent receives a message, which is to confirm these results. 

Once the opponent confirms, the results are used to calculate skill rating score. For now the rating should be very simple: everyone starts with 1000 points. win adds 10, lose subtracts 10, draw does nothing. (this algorithm will be redesigned later)

There should be a public official match history, showing all official matches, and a player ranking. 

## Friend management and messaging

- Search friends, send requests, accept requests, message friends, see friend profile, rate friend out of 5 stars (based on behaviour, not tennis skill). 

## AI 

This section collects game style data about each player. Including:
- Game feedback from friends (forehand, backhand, serving, slicing, volley, movement, etc. feedback)
- Upload your own photos or videos

Then talk to an AI that processes the game style data, to obtain training plans, or explain feedback.

## Profile management

- Verify identity by introducing real name and student id
- Self reported tennis level: (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5+)
- See behavior rating score 
- See skill rating score


Let me know if you need me to clarify anything.  Write a markdown file in English describing the platform. This markdown file will then be used by coding agents to develop the app.