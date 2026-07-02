# ProxyIP按地区分类高优筛选订阅
import json
import urllib.request
import urllib.error

def generate_ips_from_api():
    # ------------------ 配置区域 ------------------
    # 定义你需要独立生成文件的国家/地区列表
    TARGET_COUNTRIES = ["HK", "SG", "TW", "JP", "KR"]
    
    # 高优 ASN 筛选列表
    TARGET_ASNS = None
    
    # 指定端口筛选
    TARGET_PORT = None

    # 数据源 API 接口
    API_URL = "https://zip.cm.edu.kg/all.json"
    # ---------------------------------------------

    request_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    print(f"建立网络连接: 开始抓取目标接口 data {API_URL} ...")
    try:
        req = urllib.request.Request(API_URL, headers=request_headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html_content = response.read().decode("utf-8")
            raw_data = json.loads(html_content)
    except urllib.error.URLError as e:
        print(f"网络连接失败: 无法访问 API 接口，错误原因: {e}")
        return
    except json.JSONDecodeError:
        print("数据解析失败: 接口返回的数据不是有效的 JSON 格式。")
        return
    except Exception as e:
        print(f"发生未知错误: {e}")
        return

    node_data_list = []
    if isinstance(raw_data, list):
        node_data_list = raw_data
    elif isinstance(raw_data, dict):
        for key, value in raw_data.items():
            if isinstance(value, list):
                node_data_list.extend(value)
            elif isinstance(value, dict):
                node_data_list.append(value)
    else:
        print("数据结构异常: 无法识别的 JSON 骨架类型。")
        return

    print(f"接口数据拉取成功: 准备分析总计 {len(node_data_list)} 条原始数据...")

    # 🟢 核心改动：外层循环遍历每一个目标国家
    for country_code in TARGET_COUNTRIES:
        seen_ips = set()
        final_ip_lines = []
        output_filename = f"ProxyIP-{country_code}.txt" # 动态生成文件名，如 ProxyIP-SG.txt

        for item in node_data_list:
            if not isinstance(item, dict):
                continue

            meta_data = item.get("meta", {})
            if not isinstance(meta_data, dict):
                meta_data = {}

            country = meta_data.get("country", "UNKNOWN")
            asn = meta_data.get("asn", "UNKNOWN")

            port = item.get("_port") or item.get("port")
            if isinstance(port, list) and len(port) > 0:
                port = port[0]

            if port is None:
                continue

            # 精确匹配当前循环的国家
            if country != country_code:
                continue
                
            if TARGET_ASNS and asn not in TARGET_ASNS:
                continue
                
            if TARGET_PORT and int(port) != TARGET_PORT:
                continue
            
            v4_ip = item.get("ip")
            v6_ip = meta_data.get("clientIp")
            
            node_ips = []
            if v4_ip:
                node_ips.append(v4_ip)
            if v6_ip:
                node_ips.append(v6_ip)
                
            if not node_ips:
                continue
                
            for current_ip in node_ips:
                if current_ip in seen_ips:
                    continue

                seen_ips.add(current_ip)
                
                # 格式化输出
                ip_line = f"{current_ip}:{port}#{country}-{asn}\n"
                final_ip_lines.append(ip_line)

        total_ips = len(final_ip_lines)
        print(f"【{country_code}】筛选完成: 共筛出 {total_ips} 个独立合规 IP。")

        # 为当前国家写入独立文件
        if total_ips > 0:
            try:
                with open(output_filename, "w", encoding="utf-8") as f:
                    f.writelines(final_ip_lines)
                print(f"成功保存文件: {output_filename}")
            except IOError as e:
                print(f"写入文件失败 {output_filename}: {e}")
        else:
            print(f"未筛选到 {country_code} 的节点，跳过生成文件。")

if __name__ == "__main__":
    generate_ips_from_api()
