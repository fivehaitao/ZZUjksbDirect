
import json
import smtplib
import time
from collections import defaultdict
from email.mime.text import MIMEText

# 创建发送邮件的方法

admin_log = []
user_log = defaultdict(list)

def add_admin_log(log):
    admin_log.append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ': ' + log)


def add_user_log(user_info, log):

    user_log[user_info['mail_target']].append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ': ' + log)

    add_admin_log(user_info['real_name'] + ': '+log)

def processUserInfo(processing_pool):
    # 分割多用户列表解析
    if "！" in processing_pool:
        user_pool = processing_pool.split("！")
        add_admin_log("当前用户数量为 " + str(len(user_pool)))
    else:
        user_pool = [processing_pool]
    users=[]
    for i, pop_user in enumerate(user_pool):
        user_info = {}
        this_user = pop_user.split("，")
        # 单个用户信息检查
        if len(this_user) < 6:
            add_admin_log("用户" + str(i) + "池配置有误，必须重新配置！此用户信息条目数量少于6，将被忽略.")
            continue
        user_info['user_id'] = this_user[0]
        user_info['user_pd'] = this_user[1]
        user_info['city_code'] = this_user[2]
        user_info['location'] = this_user[3]
        user_info['real_name'] = this_user[4]
        user_info['mail_target'] = this_user[5]
        if len(this_user) == 7:  # 当存在疫苗接种情况可选项时取其值，当值不在指定范围时忽略
            if (this_user[6] == "1") or (this_user[6] == "2") or (this_user[6] == "3") or (this_user[6] == "4"):
                user_info['myvs_26'] = this_user[6]
        users.append(user_info)
    return users


def report_mail(send_mail_info, receive_mail_address, msg):
    with open("mail_public_config.json", 'rb') as file_obj_inner:
        public_mail_config = json.load(file_obj_inner)
        file_obj_inner.close()
    # 配置邮件内容
    mail_id = send_mail_info['mail_id']
    mail_pd = send_mail_info['mail_pd']
    mail_message = MIMEText(str(msg), 'plain', 'utf-8')
    mail_message['Subject'] = public_mail_config['title']
    mail_message['From'] = mail_id
    mail_message['To'] = receive_mail_address
    # 尝试发送邮件
    try:
        mail_host = "Zero"
        mail_port = "0"
        this_host = "Zero"
        for each_host in public_mail_config["symbol"]:
            if each_host in mail_id:
                mail_host = public_mail_config[each_host]["host"]
                mail_port = public_mail_config[each_host]["port"]
                this_host = each_host
                break
        if mail_host == "Zero":
            print('发送结果的邮箱设置异常，请在 mail_public_config.json 中检查邮箱的域名配置，以及发信SMTP服务器配置.')
            raise smtplib.SMTPException
        if this_host == "Zero":
            print('发送结果的邮箱设置异常，请确保 mail_public_config.json 中包含您的邮箱配置.')
            raise smtplib.SMTPException
        if "encryption" in public_mail_config[this_host].keys():
            smtp_obj = smtplib.SMTP(mail_host, mail_port)
            smtp_obj.ehlo()
            smtp_obj.starttls()
            smtp_obj.ehlo()
            smtp_obj.login(mail_id, mail_pd)
            smtp_obj.sendmail(mail_id, receive_mail_address, mail_message.as_string())
            smtp_obj.quit()
            add_admin_log('用户邮箱' + str(receive_mail_address) + '提示信息已发送，内容包含个人敏感信息，请勿泄露邮件内容.')
        else:
            smtp_obj = smtplib.SMTP_SSL(mail_host, mail_port)
            smtp_obj.login(mail_id, mail_pd)
            smtp_obj.sendmail(mail_id, receive_mail_address, mail_message.as_string())
            smtp_obj.quit()
            add_admin_log('用户' + str(receive_mail_address) + '具体提示信息已发送到邮箱，内容包含个人敏感信息，请勿泄露邮件内容.')
    except smtplib.SMTPException:
        print('发送结果的邮箱设置可能异常，请检查邮箱和密码配置，以及发信SMTP服务器配置.')
        raise smtplib.SMTPException


def list_to_str(list):
    res = ""
    for li in list:
        res += li+'\n'
    return res

