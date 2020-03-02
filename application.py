import os
import base64

from flask import Flask
from flask import request
from flask import abort

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkiot.request.v20180120.PubRequest import PubRequest

from linebot import LineBotApi
from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent
from linebot.models import TextMessage
from linebot.models import TextSendMessage

app = Flask(__name__)

# LineBot Access Token
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]

# AliCloud Access Token
ALICLOUD_ACCESS_KEY = os.environ["ALICLOUD_ACCESS_KEY"]
ALICLOUD_ACCESS_SECRET = os.environ["ALICLOUD_ACCESS_SECRET"]
ALICLOUD_REGION = os.environ["ALICLOUD_REGION"]
ALICLOUD_IOT_PRODUCTKEY = os.environ["ALICLOUD_IOT_PRODUCTKEY"]
ALICLOUD_IOT_TOPIC = os.environ["ALICLOUD_IOT_TOPIC"]

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# create AcsClient instance
client = AcsClient(ALICLOUD_ACCESS_KEY, ALICLOUD_ACCESS_SECRET, ALICLOUD_REGION)

# callback()
@app.route("/callback", methods=['POST'])
def callback():
  # Get X-Line-Signature header value
  signature = request.headers['X-Line-Signature']

  # Get request body as text
  body = request.get_data(as_text=True)
  app.logger.info("Request body: " + body)

  # Handle webhook body
  try:
    handler.handle(body, signature)
  except InvalidSignatureError:
    abort(400)

  return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
  
  message = event.message.text
  message_bytes = message.encode('utf-8')
  base64_bytes = base64.b64encode(message_bytes)
  base64_message = base64_bytes.decode('utf-8')

  request = PubRequest()
  request.set_accept_format('json')
  request.set_TopicFullName(ALICLOUD_IOT_TOPIC)
  request.set_MessageContent(base64_message)
  request.set_ProductKey(ALICLOUD_IOT_PRODUCTKEY)
  request.set_Qos("0")
  client.do_action_with_exception(request)
  #result = str(response)
  if message == 1:
    line_bot_api.reply_message(
      event.reply_token,
      TextSendMessage(text="電気をつけました")
    )
  elif message == 0:
    line_bot_api.reply_message(
      event.reply_token,
      TextSendMessage(text="電気を消しました")
    )

if __name__ == "__main__":
  callback()
  app.run()
