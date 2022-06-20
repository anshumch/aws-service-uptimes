# ########################################################################
# Disclaimer:
# Code for example use only, not for production use
# This code has not been thoroughly tested under all conditions so,
# please do your own verification before using this code.
#
# Amazon Web Services makes no warranties, express or implied, in this document.
# Amazon Web Services (AWS) may have patents, patent applications, trademarks,
# copyrights, or other intellectual property rights covering subject matter in
# this document. Except as expressly provided in any written license agreement
# from AWS, our provision of this document does not give you any license to these
# patents, trademarks, copyrights, or other intellectual property. The descriptions
# of other companies products in this document, if any, are provided only as a
# convenience to you. Any such references should not be considered an endorsement
# or support by AWS. AWS cannot guarantee their accuracy, and the products may
# change over time. Also, the descriptions are intended as brief highlights to aid
# understanding, rather than as thorough coverage. For authoritative descriptions
# of these products, please consult their respective manufacturers.
# Copyright © 2022 Amazon Web Services, Inc. and/or its affiliates. All rights reserved.
# ########################################################################

import json
from sre_constants import MAXREPEAT
import boto3
from datetime import date,datetime

clientShd = boto3.client('health')

def lambda_handler(event, context):
    regionServicesUptimeList = []
    
    print(event)
    
    # eventInput = json.loads(event.get("body"))
    eventInput = event
    
    
    if(eventInput.get("eventDateFrom") and eventInput.get("eventDateTo") and eventInput.get("regions")):
        eventDateFrom = eventInput.get("eventDateFrom")
        eventDateTo = eventInput.get("eventDateTo")
        regions = eventInput.get("regions")
    elif(eventInput.get("body")):
        eventInputBody = json.loads(eventInput.get("body"))
        eventDateFrom = eventInputBody.get("eventDateFrom")
        eventDateTo = eventInputBody.get("eventDateTo")
        regions = eventInputBody.get("regions")
    
    regionsToSearch = []
    for region in regions:
        regionsToSearch.append(region)

    regionsToSearch.append("global")
    
    # print(eventDateFrom)
    # print(eventDateTo)
    
    regionEventServicesList = []
    
    events = getShdEvents(eventDateFrom, eventDateTo, regionsToSearch)
    print(events)
    
    
    for eventItem in events:
        print(eventItem)
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
        
        if(region in regions
            or region == "global"):
            regionEventService = {}
            regionEventService["region"] = region
            regionEventService["service"] = service
            regionEventService["startTime"] = eventItem.get("startTime")
            regionEventService["endTime"] = eventItem.get("endTime")
            regionEventService["eventPeriod"] = eventPeriodSec
            regionEventServicesList.append(regionEventService)
        
    for regionItem in regions:
        servicesUptime = findServices()
    
        servicesUptime = fillServicesUptime(regionItem, servicesUptime, regionEventServicesList, eventDateFromDt, eventDateToDt)
        
        regionServicesUptime = {}
        regionServicesUptime["region"] = regionItem
        regionServicesUptime["services"] = servicesUptime
        regionServicesUptimeList.append(regionServicesUptime)
        
      
    for regionEventService in regionEventServicesList:
        regionEventService["eventPeriod"] = str(regionEventService["eventPeriod"]) + " sec"

    requestInput = {}
    requestInput["eventDateFrom"] = eventDateFrom
    requestInput["eventDateTo"] = eventDateTo
    requestInput["regions"] = regions
    
    responseServicesUptime = {}
    responseServicesUptime["input"] = requestInput
    responseServicesUptime["regionWiseServicesUptime"] = regionServicesUptimeList
    responseServicesUptime["regionEventServicesList"] = regionEventServicesList
    responseServicesUptime["disclaimer"] = "This does not reflect any SLA commitments as SLA for each service incorporates factors other than just the Service Uptimes. This result is just an illustration for the Service Uptime vis-a-vis the time period and the AWS regions specified in the input"
    
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps(responseServicesUptime, default=str)
    }

def getShdEvents(eventDateFrom, eventDateTo, regions):
    responseEventsList = []
    nextTokenAvailable = True
    nextToken = None
    while(nextTokenAvailable):
        if(nextToken):
            responseEvents = clientShd.describe_events(
                filter={
                    'eventTypeCategories': [
                        'issue',
                    ],
                    'startTimes': [
                        {
                            'from': eventDateFrom,
                            'to': eventDateTo
                        }
                    ],
                    'regions': regions
                },
                nextToken=nextToken,
                maxResults=100
            )
        else:
            responseEvents = clientShd.describe_events(
                filter={
                    'eventTypeCategories': [
                        'issue',
                    ],
                    'startTimes': [
                        {
                            'from': eventDateFrom,
                            'to': eventDateTo
                        }
                    ],
                    'regions': regions
                },
                maxResults=100
            )

        events = responseEvents.get("events")

        for event in events:
            if(event.get("eventScopeCode") == "PUBLIC"):
                responseEventsList.append(event)
    
        nextToken = responseEvents.get("nextToken")
        
        if(nextToken != None):
            nextTokenAvailable = True
        else:
            nextTokenAvailable = False
    
    return responseEventsList

def calculateUptime(eventDateFromDt, eventDateToDt, eventPeriodSec):
    totalPeriod = (eventDateToDt - eventDateFromDt)
    totalPeriodSec = totalPeriod.total_seconds()
    # print(totalPeriodSec)
    
    return (1 - (eventPeriodSec/totalPeriodSec)) * 100
        
def findServices():
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
        serviceUptime["events"] = None
        servicesUptime.append(serviceUptime)
        
    return servicesUptime
    
def fillServicesUptime(region, servicesUptime, regionEventServicesList, eventDateFromDt, eventDateToDt):
    # print("region:" + region)
    for service in servicesUptime:
        events = []
        totalDownTimeSec = 0
        
        for regionEventService in regionEventServicesList:
            if((regionEventService.get("region") == region 
                or regionEventService.get("region") == "global")
                and regionEventService.get("service") == service.get("service")):
                    totalDownTimeSec = totalDownTimeSec + regionEventService.get("eventPeriod")
                    events.append(regionEventService)
        
        if(totalDownTimeSec > 0):
            service["uptime"] = calculateUptime(eventDateFromDt, eventDateToDt, totalDownTimeSec)    
        else: 
            service["uptime"] = 100
   
        service["uptime"] = str(service["uptime"]) + "%"
        service["events"] = events
        
    return servicesUptime
