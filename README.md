# aws-service-uptimes

## The tool enables an user to track an AWS service uptime in terms of % wrt. to Public LSE for a time period

Steps to deploy:

- Clone the repo
````bash
https://github.com/anshumch/aws-service-uptimes.git
````
- Run the following command (pre-requisite - you need to download and install [SAM CLI)](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html):
````bash
sam deploy --guided
````
- Pass the following values:

![image](https://user-images.githubusercontent.com/100800132/168960174-2d1ef7ad-e013-4293-b8df-878f1555cf7c.png)

- Once the stack is deployed, you will receive an output with stack successful creation message. Note the API output value. We will call this API endpoint to execute the lambda to fetch service wide uptimes.

![image](https://user-images.githubusercontent.com/100800132/169313945-b6e5b86d-f3dc-4a25-a890-4d6375b8dfa6.png)

- To run it:
 
![image](https://user-images.githubusercontent.com/100800132/169219355-3b124b4b-47d0-4303-bcec-23137f617780.png)


