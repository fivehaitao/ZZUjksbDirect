# jksbDirect
#
# By Clok Much
import sys

import requests

from utils.util import *

# ###### 调试区，项目可稳定使用时，两者均应是 False
# 调试开关 正常使用请设定 False ，设定为 True 后会输出更多调试信息，且不再将真实姓名替换为 喵喵喵


# 开始时接收传入的 Secrets
mail_id = sys.argv[1]
mail_pd = sys.argv[2]
admin_mail_addr = sys.argv[3]
user_pool = sys.argv[4]
# 第 3 个参数传递多用户填报信息，格式如下：
# "学号，密码，城市码，地理位置，真实姓名，反馈邮箱（接收邮件），可选的疫苗接种情况！学号2，密码2，城市码2，地理位置2..."
# 以中文逗号分隔，子项目不得包含中文逗号和中文感叹号，每个用户以中文感叹号分割
send_mail_info={'mail_id':mail_id,'mail_pd':mail_pd}
users = processUserInfo(user_pool)

for this_user in users:
    this_mail_id = this_user['mail_target']
    continue_flag=True

    # 数据准备
    uid = this_user['user_id']
    upd = this_user['user_pd']
    city_code = this_user['city_code']
    location = this_user['location']
    real_name = this_user['real_name']
    mail_address = this_user['mail_target']

    with open("config.json", "rb") as file_obj:
        personal_data = json.load(file_obj)
        file_obj.close()
    personal_data['myvs_13a'] = city_code[:2]
    personal_data['myvs_13b'] = city_code
    personal_data['myvs_13c'] = location
    personal_data['myvs_26'] = this_user['myvs_26']

    step_1_calc = 0
    step_1_output = False
    step_1_state = False
    step_2_calc = 0
    step_2_output = False
    step_2_state = False
    step_3_calc = 0
    step_3_output = False
    step_3_state = False
    result = 0
    result_flag = 0
    response = False
    mixed_token = False
    all_input = sys.argv

    # 准备请求数据
    session = requests.session()
    info = {}
    header = {"Origin": "https://jksb.v.zzu.edu.cn",
              "Referer": "https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/first0",
              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.56",
              "Host": "jksb.v.zzu.edu.cn"
              }
    post_data = {"uid": uid,
                 "upw": upd,
                 "smbtn": "进入健康状况上报平台",
                 "hh28": "722",
                 }
    step_2_data = {'day6': 'b',
                   'did': '1',
                   'men6': 'a'
                   }

    # 第一步 获取 token
    while step_1_calc < 4:
        if not continue_flag:
            break
        try:
            # 接收回应数据
            response = session.post("https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/login", data=post_data,
                                    headers=header,
                                    verify=False)
            if type(response) == requests.models.Response:
                response.encoding = "utf-8"
                step_1_output = response.text
                if "验证码" in step_1_output:
                    add_admin_log(real_name+"运行时返回需要验证码，将终止本次打卡，您需要在 Action 中合理配置运行时间.")
                    continue_flag = False
                mixed_token = response.text[response.text.rfind('ptopid'):response.text.rfind('"}}\r''\n</script>')]
                if "hidden" in mixed_token:
                    step_1_calc += 1
                    continue
                elif not mixed_token:
                    step_1_calc += 1
                    continue
                else:
                    token_ptopid = mixed_token[7:mixed_token.rfind('&sid=')]
                    token_sid = mixed_token[mixed_token.rfind('&sid=') + 5:]
                    step_1_state = True
                    personal_data['ptopid'] = token_ptopid
                    step_2_data['ptopid'] = token_ptopid
                    personal_data['sid'] = token_sid
                    step_2_data['sid'] = token_sid
                    break
            else:
                if step_1_calc < 3:
                    step_1_calc += 1
                    add_user_log(this_user, "获取 token 中" + str(step_1_calc)
                          + "次失败，没有response，可能学校服务器故障，或者学号或密码有误，请检查返回邮件信息.")
                    continue
                else:
                    add_user_log(this_user, "获取 token 中" + str(step_1_calc)
                          + "次失败，没有response，可能学校服务器故障，或者学号或密码有误，次数达到预期，终止本次打卡，报告失败情况.")
                    continue_flag = False

        except requests.exceptions.SSLError:
            if step_1_calc < 3:
                step_1_calc += 1
                add_user_log(this_user, "获取 token 中" + str(step_1_calc)
                      + "次失败，服务器提示SSLError，可能与连接问题有关.")
                continue
            else:
                add_user_log(this_user, "获取 token 中" + str(step_1_calc)
                      + "次失败，服务器提示SSLError，次数达到预期，终止本次打卡，报告失败情况.")
                continue_flag = False

    # 第二步 提交填报人
    header["Referer"] = 'https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb'
    # response = False


    while step_2_calc < 4:
        if not continue_flag:
            break
        try:
            response = session.post('https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb', headers=header,
                                    data=step_2_data,
                                    verify=False)
            if type(response) == requests.models.Response:
                response.encoding = "utf-8"
                step_2_output = response.text
                if "发热" in step_2_output:
                    break
                elif "无权" in step_2_output:
                    add_user_log(this_user,"提交填报" + str(step_2_calc)
                          + "次失败，可能是学号或密码有误，终止用户打卡，报告失败情况.")
                    continue_flag = False
                    break
                elif "验证码" in step_2_output:
                    add_user_log(this_user,"提交填报" + str(step_2_calc)
                          + "次失败，服务器返回需要验证码，可能是请求过于频繁，终止本次打卡，报告失败情况.")
                    continue_flag = False
                    break
                else:
                    add_user_log(this_user,"提交填报" + str(step_2_calc)
                          + "次失败，原因未知，终止用户打卡，报告失败情况.")
                    continue_flag = False
                    break
            else:
                if step_2_calc < 3:
                    step_2_calc += 1
                    add_user_log(this_user,"提交填报人" + str(step_2_calc)
                          + "次失败，没有response，可能学校服务器故障，或者学号或密码有误，请检查返回邮件信息.")
                    continue
                else:
                    add_user_log(this_user, "提交填报人" + str(step_2_calc)
                          + "次失败，没有response，可能学校服务器故障，次数达到预期，终止用户"
                          + str(this_user) + "打卡，报告失败情况.")
                    continue_flag = False
                    break

        except requests.exceptions.SSLError:
            if step_2_calc < 3:
                step_2_calc += 1
                add_user_log(this_user, "提交填报人" + str(step_2_calc)
                      + "次失败，服务器提示SSLError，可能与连接问题有关.")
                continue
            else:
                add_user_log(this_user, "提交填报人" + str(step_2_calc)
                      + "次失败，服务器提示SSLError，次数达到预期，终止本次打卡，报告失败情况.")
                continue_flag = False
                break

    # 第三步 提交表格
    # response = False
    if not continue_flag:
        break


    while step_3_calc < 4:
        if not continue_flag:
            break
        try:
            response = session.post('https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb', headers=header,
                                    data=personal_data,
                                    verify=False)
            if type(response) == requests.models.Response:
                response.encoding = "utf-8"
                step_3_output = response.text
                if "感谢你今日上报" in step_3_output:
                    break
                else:
                    add_user_log(this_user, "填报表格中" + str(step_3_calc)
                          + "次失败，可能打卡平台增加了新内容，或是用户今日打卡结果已被审核而不能再修改.")
                    continue_flag = False
                    break
            else:
                if step_3_calc < 3:
                    step_3_calc += 1
                    add_user_log(this_user, "填报表格中" + str(step_3_calc)
                          + "次失败，没有response，可能学校服务器故障，或者用户学号或密码有误.")
                    continue
                else:
                    add_user_log(this_user,"填报表格中" + str(step_3_calc)
                          + "次失败，没有response，可能学校服务器故障，次数达到预期，终止用户打卡，报告失败情况.")
                    continue_flag = False
                    break
        except requests.exceptions.SSLError:
            if step_3_calc < 3:
                step_3_calc += 1
                add_user_log(this_user, "填报表格中" + str(step_3_calc)
                      + "次失败，服务器提示SSLError，可能与连接问题有关.")
                continue
            else:
                add_user_log(this_user,"填报表格中" + str(step_3_calc)
                      + "次失败，服务器提示SSLError，次数达到预期，终止用户打卡，报告失败情况.")
                continue_flag = False
                break

    # 分析上报结果
    if not continue_flag:

        break
    result = step_3_output
    if "感谢你今日上报" in result:
        result_flag = True
        add_user_log(this_user, "上报成功")
    elif "由于如下原因" in result:
        result_flag = False
        add_user_log(this_user, "该用户上报失败！！代码需要更新，返回提示有新增或不匹配项目，或是今日已被审核\n"+"具体原因: "+result)
        continue_flag = False
        break
    elif "重新登录" in result:
        result_flag = False
        add_user_log(this_user, "该用户上报失败！！可能是用户名或密码错误，或服务器响应超时.")
        continue_flag = False
        break

    else:
        result_flag = False
        add_user_log(this_user, "该用户上报失败！！原因未知，请自行检查返回结果和邮件中的变量输出.")
        continue_flag = False
        break

    if not continue_flag:
        add_user_log(this_user, "该用户上报失败！！原因未知，请自行检查返回结果和邮件中的变量输出.")
    # if user_log[this_mail_id]!='':
    #     # report_mail(this_user, str(user_log[this_mail_id]))

print("user log:")
for this_user in users:
    mail_target = this_user['mail_target']
    if len(user_log[mail_target]) >0 :
        print(this_user['real_name']+":")
        print(list_to_str(user_log[mail_target]))
        report_mail(send_mail_info,mail_target,list_to_str(user_log[mail_target]))
print("admin log:")
print(list_to_str(admin_log))
report_mail(send_mail_info,admin_mail_addr,list_to_str(admin_log))

