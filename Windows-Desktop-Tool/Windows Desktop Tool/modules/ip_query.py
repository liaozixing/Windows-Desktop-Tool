import requests
import json

def get_public_ip_info():
    """
    获取当前公网IP地址及其详细信息
    采用多数据源备份机制，优先使用国内高精度接口
    """
    # 数据源1: 太平洋电脑网 (国内高精度)
    try:
        response = requests.get("http://whois.pconline.com.cn/ipJson.jsp?json=true", timeout=5)
        if response.status_code == 200:
            # 太平洋电脑网返回的可能是 GBK 编码，手动设置
            response.encoding = 'gbk'
            data = response.json()
            if not data.get("err"):
                return {
                    "status": "success",
                    "ip": data.get("ip"),
                    "country": "中国",
                    "region": data.get("pro"),
                    "city": data.get("city"),
                    "isp": data.get("addr").strip(),
                    "source": "pconline"
                }
    except Exception as e:
        print(f"pconline 接口调用失败: {e}")

    # 数据源2: ip-api.com (全球通用)
    try:
        response = requests.get("http://ip-api.com/json/?lang=zh-CN", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return {
                    "status": "success",
                    "ip": data.get("query"),
                    "country": data.get("country"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "isp": data.get("isp"),
                    "source": "ip-api"
                }
    except Exception as e:
        print(f"ip-api 接口调用失败: {e}")

    return {"status": "fail", "message": "所有IP查询接口均不可用"}

if __name__ == "__main__":
    print(get_public_ip_info())
