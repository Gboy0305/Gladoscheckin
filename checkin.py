import requests
import json
import os
from pypushdeer import PushDeer

# 定义一个函数来清理请求头中的值
def clean_header_value(value):
    if value is None:
        return ""
    value = value.strip()
    value = value.replace('\n', '').replace('\r', '').replace('\t', '')
    return value

# 主程序
if __name__ == '__main__':
    # pushdeer key 申请地址 https://www.pushdeer.com/product.html
    sckey = os.environ.get("SENDKEY", "")

    # 推送内容
    title = ""
    success, fail, repeats = 0, 0, 0        # 成功账号数量 失败账号数量 重复签到账号数量
    context = ""

    # glados账号cookie 直接使用数组 如果使用环境变量需要字符串分割一下
    cookies = os.environ.get("COOKIES", "").split("&")
    
    if cookies[0] != "":
        check_in_url = "https://glados.space/api/user/checkin"        # 签到地址
        status_url = "https://glados.space/api/user/status"          # 查看账户状态

        referer = 'https://glados.space/console/checkin'
        origin = "https://glados.space"
        useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
        payload = {
            'token': 'glados.one'
        }

        for cookie in cookies:
            # 清理请求头中的值
            cookie = clean_header_value(cookie)
            referer = clean_header_value(referer)
            origin = clean_header_value(origin)
            useragent = clean_header_value(useragent)

            # 发送签到请求
            checkin = requests.post(
                check_in_url,
                headers={
                    'cookie': cookie,
                    'referer': referer,
                    'origin': origin,
                    'user-agent': useragent,
                    'content-type': 'application/json;charset=UTF-8'
                },
                data=json.dumps(payload)
            )
            
            # 发送状态检查请求
            state = requests.get(
                status_url,
                headers={
                    'cookie': cookie,
                    'referer': referer,
                    'origin': origin,
                    'user-agent': useragent
                }
            )

            message_status = ""
            points = 0
            message_days = ""
            email = ""

            if checkin.status_code == 200:
                # 解析返回的json数据
                check_result = checkin.json().get('message', '')
                points = checkin.json().get('points', 0)
                print(f"Check-in Response: {checkin.json()}")

                if state.status_code == 200:
                    result = state.json()
                    leftdays = int(float(result.get('data', {}).get('leftDays', 0)))
                    email = result.get('data', {}).get('email', '')
                    print(f"Status Response: {result}")

                    if "Checkin! Got" in check_result:
                        success += 1
                        message_status = "签到成功，会员点数 + " + str(points)
                    elif "Checkin Repeats!" in check_result:
                        repeats += 1
                        message_status = "重复签到，明天再来"
                    else:
                        fail += 1
                        message_status = "签到失败，请检查..."
                    
                    if leftdays is not None:
                        message_days = f"{leftdays} 天"
                    else:
                        message_days = "error"
                else:
                    message_status = "状态请求失败, 请检查..."
                    message_days = "error"
            else:
                message_status = "签到请求失败, 请检查..."
                message_days = "error"

            context += f"账号: {email}, P: {points}, 剩余: {message_days} | "

        # 推送内容
        title = f'Glados, 成功{success},失败{fail},重复{repeats}'
        print("Send Content:\n", context)
    else:
        # 推送内容
        title = f'# 未找到 cookies!'
        context = "请检查环境变量中的 COOKIES 是否正确设置。"

    # 推送消息
    if sckey:
        pushdeer = PushDeer(pushkey=sckey)
        pushdeer.send_text(title, desp=context)
    else:
        print("未设置 SENDKEY，无法推送消息。")
