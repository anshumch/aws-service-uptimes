import json
import boto3
from datetime import date,datetime

clientShd = boto3.client('health')
def lambda_handler(event, context):
    # print(event)
    eventInput = json.loads(event.get("body"))
    
    eventDateFrom = eventInput.get("eventDateFrom")
    eventDateTo = eventInput.get("eventDateTo")
    
    # print(eventDateFrom)
    # print(eventDateTo)
    
    eventServicesList = []
    
    responseEvents = getShdEvents(eventDateFrom, eventDateTo)
    events = responseEvents.get("events")
    print(events)
    
    for event in events:
        eventPeriod = None
        
        # print(datetime.now())
        # print(datetime.now().replace(tzinfo=None))
        
        service = event.get("service")
        region = event.get("region")
        
        # event["endTime"] = None
        if(event.get("endTime") != None and event.get("startTime") != None):
            eventPeriod = (event.get("endTime").replace(tzinfo=None) - event.get("startTime").replace(tzinfo=None))
        elif(event.get("startTime") != None):
            eventPeriod = datetime.now().replace(tzinfo=None) - event.get("startTime").replace(tzinfo=None)
        
        if(eventPeriod != None):
            eventPeriodSec = eventPeriod.total_seconds()
        
        eventDateFromDt=datetime.strptime(eventDateFrom, "%m-%d-%Y")
        eventDateToDt=datetime.strptime(eventDateTo, "%m-%d-%Y")
        
        serviceRegion = {}
        serviceRegion["region"] = region
        serviceRegion["service"] = service
        serviceRegion["eventPeriod"] = eventPeriodSec
        serviceRegion["upTime"] = calculateUptime(eventDateFromDt, eventDateToDt, eventPeriodSec)
        
        # print(serviceRegion)
        if not any((item.get("region") == region and item.get("service") == service) for item in eventServicesList):
           eventServicesList.append(serviceRegion)
        else:
            serviceRegionExists = next((item for item in eventServicesList if (item.get("region") == region and item.get("service") == service)), None)
            serviceRegionExists["eventPeriod"] = serviceRegionExists["eventPeriod"] + eventPeriodSec
            serviceRegionExists["upTime"] = calculateUptime(eventDateFromDt, eventDateToDt, serviceRegionExists["eventPeriod"])
        
    for serviceRegion in eventServicesList:
        serviceRegion["eventPeriod"] = str(serviceRegion["eventPeriod"]) + " sec"
        serviceRegion["upTime"] = str(serviceRegion["upTime"]) + "%"
        
            
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps(eventServicesList, default=str)
    }

def getShdEvents(eventDateFrom, eventDateTo):
    responseEvents = clientShd.describe_events(
            filter={
                'eventTypeCategories': [
                    'issue',
                ],
                'startTimes': [
                    {
                        'from': eventDateFrom,
                        'to': eventDateTo
                    },
                ]
            }
        )
    return responseEvents

def calculateUptime(eventDateFromDt, eventDateToDt, eventPeriodSec):
    totalPeriod = (eventDateToDt - eventDateFromDt)
    totalPeriodSec = totalPeriod.total_seconds()
    # print(totalPeriodSec)
    
    return (1 - (eventPeriodSec/totalPeriodSec)) * 100
        
        