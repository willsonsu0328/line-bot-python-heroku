# encoding: utf-8
import sys, requests, json, os

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FollowEvent, UnfollowEvent, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, MessageTemplateAction, URITemplateAction, PostbackEvent, ConfirmTemplate
)
from linebot.exceptions import LineBotApiError

app = Flask(__name__)


LINE_CHANNEL_ACCESSTOKEN = os.environ.get('ChannelAccessToken', None)
LINE_CHANNEL_SECRET = os.environ.get('ChannelSecret', None)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESSTOKEN) #Your Channel Access Token
handler = WebhookHandler(LINE_CHANNEL_SECRET) #Your Channel Secret

def airQuality(areaName):

    url = 'https://pm25.lass-net.org/data/last-all-epa.json'
    response = requests.get(url)
    response.raise_for_status()

    airDataInfo = json.loads(response.text)

    p(airDataInfo)
    airDataList = airDataInfo['feeds']
    status =''
    pmData =''
    for airDict in airDataList:
        dicAreaStr = airDict['SiteName']
        if areaName in dicAreaStr:
            status = airDict['Status'] 
            pmData = airDict['PM2_5']
            break

    return pmData, status

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    p("Request body: " + body);

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(FollowEvent)
def follow(event):
    p("follow event.type: "+event.type)

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text #message from user

    p("event.reply_token: "+event.reply_token)
    p("event.type: "+event.type)
    p("event.source.userId: "+event.source.user_id)

    try:
        profile = line_bot_api.get_profile(event.source.user_id)
        p("profile.display_name: "+profile.display_name)
        p("profile.user_id: "+profile.user_id)
        p("profile.picture_url: "+profile.picture_url)
        if len(profile.display_name) == 0:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='加我為朋友，才告訴你唷！'))
    except LineBotApiError as e:
        #line_bot_api.reply_message(
            #event.reply_token,
            #TextSendMessage(text='咦～尋找你的資料好像有點問題～'))
            return 'Line reply_token 檢核,不作回應';

    #Line 系統token 不回應
    if event.reply_token == '00000000000000000000000000000000':
       return 'Line reply_token 檢核,不作回應';

    if 'pm2.5' in text:
        allTexts = text.split(' ',1)

        areaName = allTexts[1]

        p("text:"+areaName);

        pmData, status = airQuality(areaName)
        pmDataStr = str(pmData)
        replyText = ''
        if len(pmDataStr) > 0:

            p("text:"+areaName + '的 pm2.5 為 '+ pmDataStr +'，' + '狀態 : ' + status);

            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='哈囉 '+profile.display_name+' 以下是你要的資料～'+'\n\n'+areaName + '的 pm2.5 為 '+ pmDataStr +'，' + '狀態 : ' + status))
        else:
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='沒有找到你要的唷～'))

    if 'shorturl' in text:

        accessToken = '98b31424caa7c30088c2bf1546adc525c9632ced'
        postURL = "http://api.pics.ee/v1/links/?access_token="+accessToken

        allTexts = text.split(' ',1)

        originalURL = allTexts[1]

        payload = {'externalId': '22695', 'url': originalURL}
        header = {'Content-type': 'application/json'}
        rp = requests.post(postURL, data=json.dumps(payload), headers=header)
        tempResult = rp.json()

        if 'data' in tempResult:
            shortURL = tempResult['data']['picseeUrl']
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='哈囉 '+profile.display_name+' 幫你縮好了: '+shortURL))
        else:
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='您輸入的可能不是網址或是縮網址服務壞掉了～'))

    if 'button' in text:

        message = TemplateSendMessage(
                  alt_text='Buttons template',
                  template=ButtonsTemplate(thumbnail_image_url='https://example.com/image.jpg',
                  title='Menu',
                  text='Please select',
                  actions=[PostbackTemplateAction(
                           label='postback',
                           text='postback text',
                           data='action=buy&itemid=1'
                           ),
                           MessageTemplateAction(
                           label='message',
                           text='message text'
                           ),
                           URITemplateAction(
                           label='uri',
                           uri='http://example.com/')
                           ]
                           )
                  )

        line_bot_api.reply_message(event.reply_token, message)

    if 'confirm' in text:

        confirm_template_message = TemplateSendMessage(
                                   alt_text='Confirm template',
                                   template=ConfirmTemplate(
                                   text='Are you sure?',
                                   actions=[PostbackTemplateAction(
                                            label='postback', 
                                            text='postback text',
                                            data='action=buy&itemid=1'
                                            ),
                                            MessageTemplateAction(
                                            label='message', 
                                            text='message text'
                                            )
                                            ]
                                            )
                                   )
        line_bot_api.reply_message(event.reply_token, confirm_template_message)

@handler.add(PostbackEvent)
def handle_postback(event):
    p("message type:"+event.type)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=event.postback.data))

def p(log):
  print(log) 
  sys.stdout.flush()  


import os
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=os.environ['PORT'])
    # app.run()