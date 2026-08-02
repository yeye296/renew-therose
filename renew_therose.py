#!/usr/bin/env python3

import os,re,sys,time,requests
from seleniumbase import SB

# 环境变量 
EMAIL = os.environ.get("EMAIL") or ""            # 邮箱   
PASSWORD = os.environ.get("PASSWORD") or ""      # 密码
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN") or ""  # tg通知 bot token
TG_CHAT_ID = os.environ.get("TG_CHAT_ID") or ""      # tg通知 chat_id id
PROXY_URL = os.environ.get("PROXY") or ""

BASE_URL = "https://client.therose.cloud/login"
PANEL_URL = "https://client.therose.cloud/panel?routeName=servers"
RENEW_URL = "https://client.therose.cloud/panel?routeName=cart_renew&id=2638"

# 检查必要变量
if not EMAIL or not PASSWORD:
    print("❌ 请设置环境变量 EMAIL 和 PASSWORD")
    sys.exit(1)

# 点击续期按钮
def click_extend_button(sb):
    current_url = sb.get_current_url()
    if "routeName=cart_renew" not in current_url:
        sb.open(RENEW_URL)
        sb.wait_for_ready_state_complete()
    return True, {}

    # if "routeName=servers" not in current_url:
    #     sb.open(PANEL_URL)
    #     sb.wait_for_ready_state_complete()

    # time.sleep(5)

    # selectors = [
    #     'a:contains("Extend")',          # 对应 <a> 标签
    #     'a[href*="cart_renew"]',         # 通过 href 关键词精确定位
    #     'div.server-actions a',          # 通过外层 class 定位 <a> 标签
    # ]

    # for sel in selectors:
    #     try:
    #         if sb.find_element(sel, timeout=5):
    #             print(f"✅ 找到元素，选择器: {sel}")
    #             sb.js_click(sel, timeout=5)
    #             print("✅ 点击成功")
    #             return True, {}
    #     except Exception as e:
    #         continue

    # try:
    #     span_elem = sb.find_element('span:contains("Extend")', timeout=5)
    #     # 用 JS 向上寻找最近的 <a> 标签并点击
    #     sb.driver.execute_script("arguments[0].closest('a').click();", span_elem)
    #     print("✅ 通过 JS 点击成功")
    #     return True, {}
    # except Exception as e:
    #     print(f"⚠️ JS 点击异常: {e}")

    # try:
    #     a_elem = sb.find_element('a:contains("Extend")', timeout=5)
    #     href = a_elem.get_attribute("href")
    #     print(f"✅ 成功获取 Extend 跳转链接: {href}")
    #     sb.open(href)
    #     sb.wait_for_ready_state_complete()
    #     print("✅ 跳转成功！")
    #     return True, {}
    # except Exception as e:
    #     return False, {"error": f"提取链接失败: {str(e)}"}


# 检查续期是否成功
def check_renewal_success(sb):
    """检查是否出现续期成功的提示"""
    success_selectors = [
        '.alert-success',
        '.alert.alert-success',
        'div[role="alert"].alert-success',
        'div.alert-success',
        'span:contains("successfully purchased")',
        'div:contains("successfully purchased")'
    ]
    
    print("⏳ 等待5秒检查续期结果...")
    time.sleep(5)
    
    for selector in success_selectors:
        try:
            element = sb.find_element(selector, timeout=5)
            if element:
                text = element.text
                print(f"✅ 发现成功提示！选择器: {selector}")
                print(f"📝 提示内容: {text}")
                return True, text
        except:
            continue
    
    # 如果没有找到特定选择器，检查页面源码是否包含成功关键词
    try:
        page_source = sb.get_page_source()
        if "successfully purchased" in page_source.lower():
            print("✅ 页面源码中发现 'successfully purchased' 关键词")
            return True, "服务器已成功续期"
    except:
        pass
    
    return False, "未检测到续期成功提示"

# 发送tg通知
def send_tg(token, chat_id, message):
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
        if resp.status_code == 200:
            print("📨 Telegram 通知已发送")
        else:
            print(f"❌ Telegram 发送失败: {resp.text}")
    except Exception as e:
        print(f"❌ Telegram 发送异常: {e}")

# 登录流程
def login(sb, email, password):
    print("🌐 打开登录页面...")
    print("⏳ 等待页面加载...")
    sb.open(BASE_URL)
    sb.wait_for_ready_state_complete()
    sb.sleep(1)
    print("📧 填写邮箱...")
    sb.type('#login_form_email', email, timeout=10)
    print("🔑 填写密码...")
    sb.type('#login_form_password', password, timeout=10)
    time.sleep(1) 
    print("🛡 处理 Turnstile...")
    try:
        sb.uc_gui_click_captcha()
        print("✅ Turnstile 已点击")
        time.sleep(7)
        # sb.save_screenshot("turnstile_passed.png")
    except Exception as e:
        print(f"⚠️ Turnstile 处理异常: {e}")
    print("🔑 点击登录按钮...")
    sb.uc_click('button:contains("Sign in")')
    sb.sleep(3)
    for _ in range(30):
        # 判断是否登录成功
        current_url = sb.get_current_url()
        page_title = sb.get_title() or ""
        # print(f"📄 当前 URL: {current_url} | Title: {page_title}")
        if "panel" in current_url:
            print(f"✅ 登录成功，当前 URL: {current_url} | Title: {page_title}")
            # sb.save_screenshot("login_success.png")
            return True, current_url
        time.sleep(1)

    print(f"❌ 登录失败，当前 URL: {sb.get_current_url()}")
    sb.save_screenshot("login_faild.png")
    return False, sb.get_current_url()

# 主流程
def main():
    print("🚀 启动浏览器")

    with SB(uc=True, headless=False, proxy=PROXY_URL if PROXY_URL else None) as sb:
        success, url = login(sb, EMAIL, PASSWORD)
        
        if not success:
            msg = f"❌ 登录失败"
            print(msg)
            send_tg(TG_BOT_TOKEN, TG_CHAT_ID, msg)
            sys.exit(1)

        print("📄 开始续期流程...")
        
        # 点击 Extend 按钮
        ok, info = click_extend_button(sb)
        if not ok:
            msg = f"❌ 点击 Extend 按钮失败: {info.get('error')}"
            print(msg)
            sb.save_screenshot("click_extend_faild.png")
            send_tg(TG_BOT_TOKEN, TG_CHAT_ID, msg)
            sys.exit(1)
        
        time.sleep(1)
        
        # 点击 Order now 按钮
        try:
            button = sb.find_element('button:contains("Order now")', timeout=15)
            if button:
                print("🛒 点击 Order now 按钮...")
                sb.uc_click('button:contains("Order now")')
                # sb.js_click(button, timeout=5)
                print("✅ 已点击 Order now 按钮")
            else:
                msg = "❌ 未找到 Order now 按钮"
                print(msg)
                sb.save_screenshot("click_order_faild.png")
                send_tg(TG_BOT_TOKEN, TG_CHAT_ID, msg)
                sys.exit(1)
        except Exception as e:
            msg = f"❌ 点击 Order now 失败: {e}"
            print(msg)
            sb.save_screenshot("click_order_error.png")
            send_tg(TG_BOT_TOKEN, TG_CHAT_ID, msg)
            sys.exit(1)
        
        # 检查续期是否成功
        print("🔍 检查续期结果...")
        renewal_success, renewal_msg = check_renewal_success(sb)
        
        if renewal_success:
            msg = f"✅ 续期成功！{renewal_msg}"
            print(msg)
            # sb.save_screenshot("renewal_success.png")
        else:
            msg = f"❌ 续期可能失败: {renewal_msg}"
            print(msg)
            sb.save_screenshot("renewal_failed.png")
        
        send_tg(TG_BOT_TOKEN, TG_CHAT_ID, msg)
        if not renewal_success: sys.exit(1)

    print("🏁 脚本执行完毕")

if __name__ == "__main__":
    main()
