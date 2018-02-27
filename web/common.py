import smtplib,threading,random,os,asyncio,datetime,uuid
from email.mime.text import MIMEText

#发送邮件模块
def send_mail(subject, content):
    sender = '18353367683@163.com'
    receiver = '18353367683@163.com'
    smtpserver = 'smtp.163.com'
    username = '18353367683@163.com'
    password = '520amy3y4@199@9'
    msg = MIMEText(content, 'html', 'utf-8')
    msg['Subject'] = subject
    smtp = smtplib.SMTP()
    smtp.connect(smtpserver)
    smtp.login(username, password)
    smtp.sendmail(sender, receiver, msg.as_string())
    smtp.quit()

#邮件发送，多线程
class emailThread(threading.Thread):
    def __init__(self, threadname, subject, content):
        self.subject = subject
        self.content = content
        threading.Thread.__init__(self, name=threadname)

    def run(self):
        send_mail(self.subject, self.content)


#获取随机颜色
def rand_color():
    colors = ['red', 'orange', 'yellow', 'olive', 'green', 'teal', 'blue', 'violet', 'purple', 'pink', 'brown', 'grey', 'black']
    rand_num = random.randint(0, len(colors) - 1)
    return colors[rand_num]

#保存文件
@asyncio.coroutine
def savefile(iofile, filename):
    today = datetime.date.today()
    save_path = '../upload/%s/%s/%s/' % (today.year, today.month, today.day)
    if(not os.path.exists(save_path)):
        os.makedirs(save_path)
    filename = '%s%s' % (next_id(), file_extension(filename))
    with open(os.path.join(save_path, filename), 'wb') as f:
        buf = iofile.read()  # 8192 bytes by default.
        f.write(buf)
        f.close()
    return os.path.join(save_path, filename)

#获取随机id
def next_id():
    return '%s' % ((uuid.uuid4().hex)[:32])

#获取文件后缀
def file_extension(path):
  return os.path.splitext(path)[1]