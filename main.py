#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Alex Zwetsloot; alex@zwetsloot.uk'

#Settings
#Your caldav address - you can find this in your ~/Library/Calendars folder on Mac/Calendar.app
url = "https://p18-caldav.icloud.com/1744618118/calendars/work/"
#Your (apple?) username.
user = "moi@moi"
#And the password
password="thePikachusAreComingCoverYourBumBums"

#See bottom of file to configure html styles.
dev_mode = False
#If True, will read CalDav data from caldav.pckl rather than getting it fresh from the website.

import caldav
import pytz
import time
import os.path
import pickle
from icalendar import Calendar, Event
from datetime import datetime, timedelta


def fb(item):
    if item == True:
        return "Free"
    else:
        return "Busy"

def free_or_busy(mycallist, potentialdatetime):
    #Returns true or false, True = free, False = busy
    for tempCal in mycallist:
        for component in tempCal.walk():
            if component.name == "VEVENT":
                eventEnd = component.get('dtend').dt
                eventStart = component.get('dtstart').dt
                if eventEnd.tzinfo == None:
                    eventEnd = eventEnd.replace(tzinfo=pytz.UTC)
                if eventStart.tzinfo == None:
                    eventStart = eventStart.replace(tzinfo=pytz.UTC)
                if potentialdatetime < eventEnd and potentialdatetime >= eventStart:
                    return False
                else:
                    pass
    return True

def main():
    client = caldav.DAVClient(url, username=user, password=password)
    principal = client.principal()
    calendars = principal.calendars()
    #Get a list of events (i.e raw data) and make it into calendars (icalender objects).
    eventlist = list()
    callist = list()
    #Use casting between event -> icalendar as lightly as possible, it is not fast.
    if dev_mode and os.path.isfile("./caldav.pckle"):
        openJar = open("./caldav.pckle", "rb")
        eventlist = pickle.load(openJar)
        openJar.close()
        print "Dev mode is on; using pickle instead of getting fresh data."
    else:
        for calendar in calendars:
            for event in calendar.date_search((datetime.today() - timedelta(7)), (datetime.today() + timedelta(12))):
                eventlist.append(event.data)
                callist.append(Calendar.from_ical(event.data))
        if dev_mode:
            openJar = open("./caldav.pckle", "wb")
            pickle.dump(eventlist, openJar)
            openJar.close()

    # Give me a list of lists of datetimes for days you want free/busy for.
    #
    # Example:
    # In this example, it will output two tables. One for week one Mon, tues, thurs and another table for week two, Mon,
    # Tues, Thurs. In this way you can only show availability for days you want to (i.e not weekends, or if you don't
    # work wednesday for example).
    #
    # tableList[0] = [<datetime for Mon1st>, <datetime for Tue2nd>, <datetime for Thurs4th>]
    # tableList[1] = [<datetime for Mon8th>, <datetime for Tue9th>, <datetime for Thurs5th>]
    #
    # You can populate the tableList however you like, so long as it's with datetimes, however the default action below
    # is to make two tables.
    #
    # tableList[0] will be 'this monday' (i.e start of week) and run through to 'this friday'
    # tableList[1] will be 'next monday' (i.e start of next week) and run through to 'next friday'
    #
    # N.B: Tables will generate data sequentially from the list, so make sure the progression of days makes sense.
    #
    # Configurable options:
    # Time resolution = the number of minutes between each free_busy sample. For 60, it will generate 9:00-10:00, etc.
    # Lower values will make the table bigger, but if you frequently have events that don't last a whole hour it will
    # make your fbc more accurate.

    timeResolution =  timedelta(minutes=60)

    # What time do you want to start your fbc?
    day_start = 9

    # and end it? N.B MUST BE 24hr format.
    day_end = 18

    # Generate a list of the days I want to get free/busy for.
    tableList = list()

    # This is how I populate it with wk1 Mon-Fri, wk2 Mon-Fri
    monday_at_nine = (datetime.today() - timedelta(days=datetime.today().weekday())).replace(hour=9,minute=0,second=0,microsecond=0,tzinfo=pytz.UTC)
    monday_next_week = monday_at_nine + timedelta(days=7)
    wk1list = list()
    wk2list = list()
    wk1list.append(monday_at_nine)
    wk2list.append(monday_next_week)
    for x in range(1,5):
        wk1list.append(monday_at_nine + timedelta(days=x))
        wk2list.append(monday_next_week + timedelta(days=x))
    tableList.append(wk1list)
    tableList.append(wk2list)

    #Get some html-able time values for rows
    mytimes = list()
    a_day = monday_at_nine.replace(hour=day_start)
    while a_day.hour <= day_end:
        mytimes.append(a_day.strftime("%R"))
        a_day += timeResolution

    #Get some html-able date values for columns
    columnHeaders = list()

    for table in tableList:
        tempList = list()
        for eachday in table:
            tempList.append(eachday.strftime("%a %e/%m."))
        columnHeaders.append(tempList)

    listOfTimes = list()
    #Make a list [each week] of dictionaries [each day] of lists [each time point to be sampled]
    c = 0
    for table in columnHeaders:
        daycount = 0
        tempList = list()
        tempDict = dict()
        for daylabel in range(0, len(table)):
            daycount += 1
            innerList = list()
            innerList.append(tableList[c][daylabel])
            for num in range(1, len(mytimes)-1):
                innerList.append((tableList[c][daylabel] + (timeResolution * num)))
            tempDict[columnHeaders[c][daylabel]] = innerList
        listOfTimes.append(tempDict)
        c+=1

    # This is nasty looking and has a ridiculous amount of nested lists.
    # listOfTimes = week1, week2 0, 1, 2, etc
    # listOfTimes[0] = a dictionary where "commonname": list(times to check)
    # so each individual time is listOfTimes[0]['commonname'] and each individual time is 0, 1, 2, 3 etc.
    # This format is good for us conceptually, but html tables work in rows and columns where you need to tell it
    # all of the first row, second row, etc.
    c=0
    weekList = list()
    for week in listOfTimes:
        #For each timepoint of the day
        daytimes = list()
        for t in range(0, len(mytimes)-1):
            timePoint = list()
            #For each day I have info for
            for day in sorted(week, key=week.get):
                timePoint.append(free_or_busy(callist, week[day][t]))
            daytimes.append(timePoint)
        weekList.append(daytimes)

    print "Data generated %s " % time.strftime("%d/%m %H:%M")
    c=0
    for week in weekList:
            print """
            <div id='calTab%s'>
            <table style='width:100%%;table-layout:fixed;font-size:11pt'>
            <tr>
                    <td style='text-align:right'>Day</td>""" % (c)
            for day in columnHeaders[c]:
                print """<td style='text-align:center'>%s</td>""" % (day)
            print "</tr>"
            t=0
            for row in weekList[c]:
                print """<tr>"""
                print """<td style='text-align:right'>%s-%s</td>""" % (mytimes[t], mytimes[t+1])
                t+=1
                for item in row:
                    if item == True:
                        print "<td style='background-color:#66cc66; color:#66cc66;'>" + fb(item) + "</td>"
                    else:
                        print "<td style='background-color:#ff4d4d; color:#ff4d4d;'>" + fb(item) + "</td>"
                print "</tr>"
            print "</table></div id='calTab%s'>" % (c)
            c +=1



    return

main()
