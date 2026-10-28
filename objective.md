
# THUCourt

This is a website we are trying to develop. It is a platform that will be used for students inside Tsinghua University.

Build a normal mobile-friendly website first. A WeChat Mini Program is a later phase; its delivery date is not yet specified.

Ideally, students should be able to log in using WeChat, and then submit their real name and student ID for manual verification by an administrator. Entering those fields alone does not constitute verification.


# Sections:

**grid view note:**

There are two court areas: zijing and beiguan. zijing has 14 courts. beiguan has 4 courts. The available dates are always 4: the current date and three dates into the future. The user can switch between the two court areas and 4 dates. The avalible time slots per date are as follows: 8am to 10pm (1h slots) (time slot durations might be subject to change later). So for any chosen date, zijing area grid should be 14 columns and 14 rows, while beiguan area grid should be 4 columns and 14 rows. 

**deletion note:**

All created requests can be deleted by the user that created them.

Offers and game requests support active, fulfilled, cancelled, and expired states. Creators can still delete their own requests regardless of these lifecycle states.

**contact note:**

Students may message any other student without becoming friends first. “Contact” always means internal messaging.

## Buy and sell

- Booking transfers are arranged outside THUCourt.
- Two available views: list or grid
- Sell offer list shows sell offers from all users. It contains a filtering tool (can choose time, court area, date). 
- Buy offer list shows buy offers from all users. It contains a filtering tool (can choose time, court area, date). 
- Grid mode shows the number of buy offers and sell offers on each available time slot. See the grid view note.

- By pressing on a slot, the user can choose to create a buy or sell offer or to contact a user who has already created a buy or sell offer. 

- zijing courts are 15 rmb per slot. beiguan courts are 120 rmb per slot.

## Trade

- Create trade offer using a button
- List view shows trade offers from other users in a list. It contains a filtering tool (can choose time, court area, date).
- Trade offers specify the offered area/date/time and desired area/date/time options, without requiring a court number. For example: “I have Zijing tomorrow at 18:00 and want Zijing at 20:00.” Booking transfers are arranged outside THUCourt.

## Find games

- Requests are attached to a specific court booking and include the number of players needed, singles/doubles, and a desired skill-level range.
- Two available views: list or grid
- List view shows find game requests. It contains a filtering tool (can choose time, court area, date, player level). 
- Grid mode shows find game requests on each time slot. See the grid view note. Note: grids should contain one column only. They should put all the game requests at one time slice together. 

- By pressing on a slot, the user can choose to create a find game request or to contact a user who has already created such a request. 

## Record official match score

Players decide beforehand that they will play a match that will be scored here. After playing, they record the results here. 

Support both singles and doubles matches.

When submitting results:
- Select singles or doubles, the other participants, and the teams
- Enter game scores as structured sets
- Select the winner or draw
- Select the date played

The opponent receives an internal message to confirm these results. The required confirmation policy for doubles remains to be decided.

Each player has separate singles and doubles skill ratings, each starting at 1000 points. Once the required opponent confirmation is received, apply the following simple rule only to the relevant rating type: a win adds 10 points, a loss subtracts 10 points, and a draw does nothing. This algorithm will be redesigned later.

Results without the required opponent confirmation are invalid for official history and ratings. Confirmed results cannot be corrected.

There should be an official match history showing all confirmed official matches, and player rankings for singles and doubles. These are visible only to verified Tsinghua students, not the open internet.

## Friend management and messaging

- Search friends, send requests, accept requests, and see friend profiles.
- Students can message any other student through internal messaging; friendship is not required.
- Each friend may submit one anonymous 1–5-star behavior rating per target player and edit it later. This measures behavior, not tennis skill.
- Friends can provide both written comments and numerical tennis ratings by stroke/category. Only the target player can view this feedback through the product. It may be processed by that player's private coaching service.

## AI 

This section collects game style data about each player. Including:
- Game feedback from friends, including written comments and numerical ratings by stroke/category (forehand, backhand, serving, slicing, volley, movement, etc.). Only the target player can view this feedback through the product.
- Upload your own photos or videos
- Match history and previous training plans

Then talk to an AI that processes the game style data to obtain training plans or explain feedback. Coaching is private to each player and should combine friend feedback, pictures, videos, match history, and previous training plans when available.

A suitable approach is a media-analysis stage that produces text observations from pictures and videos, followed by a coaching stage that combines those observations with the other evidence.

## Profile management

- Submit real name and student ID for manual verification by an administrator; the account is not verified until approved
- Self reported tennis level: (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5+)
- See behavior rating score 
- See separate singles and doubles skill rating scores


Let me know if you need me to clarify anything.  Write a markdown file in English describing the platform. This markdown file will then be used by coding agents to develop the app.




# Other info

Backend: django
AI model: TBD

## Remaining decisions

- Doubles confirmation: decide whether all three non-submitting players must confirm, or whether only the opposing team confirms. Until agreed, all-three confirmation is a planning proposal only.
- Define permitted set/tiebreak formats and draw rules; numerical stroke-feedback scale; whether listed court prices are fixed or editable; and whether payments, like booking transfers, are handled externally.
- Confirm team size and exact November 13 feature priorities. The final delivery is planned for mid-December; the Mini Program is not yet assigned to that deadline.
