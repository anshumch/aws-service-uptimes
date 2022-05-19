import json
import boto3
from datetime import date,datetime

clientShd = boto3.client('health')

def lambda_handler(event, context):
    regionServicesUptimeList = []
    
    print(event)
    
    eventInput = json.loads(event.get("body"))
    # eventInput = event
    
    regions = eventInput.get("regions")
    eventDateFrom = eventInput.get("eventDateFrom")
    eventDateTo = eventInput.get("eventDateTo")
    
    
    # print(eventDateFrom)
    # print(eventDateTo)
    
    regionEventServicesList = []
    
    responseEvents = getShdEvents(eventDateFrom, eventDateTo)
    events = responseEvents.get("events")
    # print(events)
    
    for eventItem in events:
        eventPeriod = None
        
        # print(datetime.now())
        # print(datetime.now().replace(tzinfo=None))
        
        service = eventItem.get("service")
        region = eventItem.get("region")
        
        # event["endTime"] = None
        if(eventItem.get("endTime") != None and eventItem.get("startTime") != None):
            eventPeriod = (eventItem.get("endTime").replace(tzinfo=None) - eventItem.get("startTime").replace(tzinfo=None))
        elif(eventItem.get("startTime") != None):
            eventPeriod = datetime.now().replace(tzinfo=None) - eventItem.get("startTime").replace(tzinfo=None)
        
        if(eventPeriod != None):
            eventPeriodSec = eventPeriod.total_seconds()
        
        eventDateFromDt=datetime.strptime(eventDateFrom, "%m-%d-%Y")
        eventDateToDt=datetime.strptime(eventDateTo, "%m-%d-%Y")
        
        if(region in regions):
            regionEventService = {}
            regionEventService["region"] = region
            regionEventService["service"] = service
            regionEventService["startTime"] = eventItem.get("startTime")
            regionEventService["endTime"] = eventItem.get("endTime")
            regionEventService["eventPeriod"] = eventPeriodSec
            regionEventServicesList.append(regionEventService)
        
    for regionItem in regions:
        servicesUptime = findServices(regionItem)  
        servicesUptime = fillServicesUptime(regionItem, servicesUptime, regionEventServicesList, eventDateFromDt, eventDateToDt)
        
        regionServicesUptime = {}
        regionServicesUptime["region"] = regionItem
        regionServicesUptime["services"] = servicesUptime
        regionServicesUptimeList.append(regionServicesUptime)
        
        responseServicesUptime = {}
        responseServicesUptime["input"] = eventInput
        responseServicesUptime["regionWiseServicesUptime"] = regionServicesUptimeList
        responseServicesUptime["regionEventServicesList"] = regionEventServicesList
        responseServicesUptime["disclaimer"] = "This does not reflect any SLA commitments as SLA for each service incorporates factors other than Service Uptimes. This result is just an illustration for the Service Uptime vis-a-vis the time period and the AWS regions specified in the input"
        
    for regionEventService in regionEventServicesList:
        regionEventService["eventPeriod"] = str(regionEventService["eventPeriod"]) + " sec"
        
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps(responseServicesUptime, default=str)
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
        
def findServices(regionItem):
    services = []
    eventTypeCodes = []
    
    nextTokenAvailable = True
    nextToken = None
    
    while nextTokenAvailable == True:
        if(nextToken):
            responseEventTypeCodes = clientShd.describe_event_types(
                    filter={
                        'eventTypeCategories': [
                            'issue',
                        ]
                    },
                    maxResults=100,
                    nextToken=nextToken
                )
            eventTypeCodes.append(responseEventTypeCodes.get("eventTypes"))
        else:
            responseEventTypeCodes = clientShd.describe_event_types(
                    filter={
                        'eventTypeCategories': [
                            'issue',
                        ]
                    },
                    maxResults=100
                )
            eventTypeCodes.append(responseEventTypeCodes.get("eventTypes"))
        
        nextToken = responseEventTypeCodes.get("nextToken")
        
        if(nextToken != None):
            nextTokenAvailable = True
        else:
            nextTokenAvailable = False
    
    # print(len(eventTypeCodes))
    eventTypeCodesFlatList = [item for eventTypeCodesList in eventTypeCodes for item in eventTypeCodesList]
    # print(len(eventTypeCodesFlatList))
    
    services = list(set(list(map(lambda x: x.get('service'), eventTypeCodesFlatList))))
    services = sorted(services)
    # print(services)
    # for eventTypeCode in eventTypeCodes:
        # print(eventTypeCode)
        # services.append(eventTypeCode.get("service"))
    
    servicesUptime = []
    for service in services:
        serviceUptime = {}
        serviceUptime["service"] = service
        serviceUptime["uptime"] = None
        servicesUptime.append(serviceUptime)
        
    return servicesUptime
    
def fillServicesUptime(region, servicesUptime, regionEventServicesList, eventDateFromDt, eventDateToDt):
    # print("region:" + region)
    for service in servicesUptime:
        totalDownTimeSec = 0
        
        for regionEventService in regionEventServicesList:
            if(regionEventService.get("region") == region 
                and regionEventService.get("service") == service.get("service")):
                    totalDownTimeSec = totalDownTimeSec + regionEventService.get("eventPeriod")
        
        if(totalDownTimeSec > 0):
            service["uptime"] = calculateUptime(eventDateFromDt, eventDateToDt, totalDownTimeSec)    
        else: 
            service["uptime"] = 100
   
        service["uptime"] = str(service["uptime"]) + "%"
        
    return servicesUptime