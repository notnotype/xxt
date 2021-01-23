from urllib.parse import quote

from requests import get, post


def main():
    headers = {'Host': 'mooc1-1.chaoxing.com', 'Connection': 'keep-alive', 'Content-Length': '134',
               'Accept': 'text/html, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest',
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4230.1 Safari/537.36',
               'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
               'Origin': 'https://mooc1-1.chaoxing.com', 'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-Mode': 'cors',
               'Sec-Fetch-Dest': 'empty',
               'Referer': 'https://mooc1-1.chaoxing.com/bbscircle/grouptopic?courseId=215085317&clazzid=33808600&ut=s&showChooseClazzId=33808600&enc=1aae138e9c06b6ebdba264f0c2876c46&chapterId=0&cpi=156496937',
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
               'Cookie': 'source=""; spaceFid=1821; spaceRoleId=""; thirdRegist=1; web_im_hxToken=YWMtUqmeKDfNEeu3iL%5fI%2dKxLqaKlE4D%2d6RHksYgJxSsb8jJZFa%5fwAkMR67k%2defI%2dKewcAwMAAAF2OGcymABPGgB14UM44cdnkkgjqVVQvKLOqP4Jv8hz2QwUzd%2dozfSgYA; web_im_tid=106990444; web_im_pic=http%3a%2f%2fphoto%2echaoxing%2ecom%2fphoto%5f80%2ejpg; web_im_name=%u848b%u4fca%u6770; KI4SO_SERVER_EC=RERFSWdRQWdsckNwckxwM2pXeFFSZkhPNUlCaTFuTW9NQWc4Q0U4bEdKNUtGbDVZSjJybStkSXd3%0ANkprU2VsMkRtU2djWlRjU2NTVQp1NG13bWtscWxmbmd6TEM0eE1Ed2V3NkQwMkI2T1pzN3dlclJt%0ARDFtdWE0OVd4bXBHSTZockJmNDRYdlVvNVZVdmpjVGZ2STd3VEh1Ck5EcWZVcTVkWFY1eHJCSGJM%0ARXc4NnFVTnBsbFR1T0dhMzl1cDR3V0NMYUpXOFk5bERvRG9ZODA4d002UEFoQkw1NWZMR1hYd3Rm%0AL3EKRXNpYXFmR0wrQzFVYXZZaytuamcwOGNodEJGR3IzZytOak1OQjlWRWxidWRBcXhLMHVkVkxF%0AUzNib2JiNDhLeU1RM0QweDNIc0hYSgpsYjVjbUhFeDFydEJQQUlWclZTUHJRUzh6dk1DVHBib3FS%0AU2g3WWRoOW54c2xkRndvZzNxZVhKVEFUWkZpSlRSSEhucE5nSk9sdWlwCkZLSHRVNWlsM2ExQlR5%0AaWRFVnk5dkxDYXorTCtWWUtXVG5DMU1lNDBPcDlTcmwyckxocXM2WDluVVU5Vk9UZSt1aTZLP2Fw%0AcElkPTEma2V5SWQ9MQ%3D%3D; _tid=106990444; sso_puid=152804638; _industry=5; k8s=04bb3a2fa969bb6c88c300a27846838f245e7c61; route=ac9a7739314fa6817cbac7e56032374b; lv=2; fid=1821; _uid=152804638; uf=b2d2c93beefa90dcd1ee03ad65e10855002362bacce7629380f5a15178273ea38bb65128213d2769e928a987d10c379d913b662843f1f4ad6d92e371d7fdf6446ece1d9f47db742bce71fc6e59483dd335db6a0037bde9fc492ed0cf3761853b967b530489478102; _d=1610086960017; UID=152804638; vc=A36411C8D18DADE1DECFFC4CD2769FF4; vc2=05DD9DEE88D13C5AA34F23BB3B3E255F; vc3=D08jKdyoG6RPIS2H0SaWLn%2B4vzdBzBcbfZ5v94gDFDhD8nnkGpbl2EcJCkXkIiXYheydyJ1fxv%2FFKS2Gfc3ZoSRO2VRU4sD9Dy%2BkQ%2BbK1mNl9H1Ci6fIxu9Op4d6ZotamOX6Ipsh9hlTSTb5C%2BYtxRuyv9xe7kxPll9Bs9fK7YU%3D34dc22b0a0bc82050b88c215bb25ad2f; xxtenc=20fa5b1fdc858614416da69204450107; DSSTASH_LOG=C_38-UN_55-US_152804638-T_1610086960018; cookiecheck=true; duxiu=userName%5fdsr%2c%3dtfm%2c%21userid%5fdsr%2c%3d23224%2c%21char%5fdsr%2c%3d%u9551%2c%21metaType%2c%3d257%2c%21dsr%5ffrom%2c%3d1%2c%21logo%5fdsr%2c%3dlogo0408%2ejpg%2c%21logosmall%5fdsr%2c%3dsmall0408%2ejpg%2c%21title%5fdsr%2c%3d%u6e56%u5357%u79d1%u6280%u5927%u5b66%2c%21url%5fdsr%2c%3d%2c%21compcode%5fdsr%2c%3d1088%2c%21province%5fdsr%2c%3d%u6e56%u5357%2c%21readDom%2c%3d%2c%21isdomain%2c%3d3%2c%21showcol%2c%3d0%2c%21hu%2c%3d0%2c%21areaid%2c%3d0%2c%21uscol%2c%3d0%2c%21isfirst%2c%3d0%2c%21istest%2c%3d0%2c%21cdb%2c%3d0%2c%21og%2c%3d0%2c%21ogvalue%2c%3d0%2c%21testornot%2c%3d1%2c%21remind%2c%3d0%2c%21datecount%2c%3d3280%2c%21userIPType%2c%3d1%2c%21my%2c%3d1%2c%21lt%2c%3d0%2c%21ttt%2c%3dfxlogin%2echaoxing%2c%21enc%5fdsr%2c%3dEC8C7BFED918E86561174FA0AE8733D8; AID_dsr=55; superlib=""; msign_dsr=1610086963817; search_uuid=5fc1480e%2de862%2d4f8a%2da6c3%2d35ce1c3be16a; mqs=19e3b526c24d63963d23bb7a0b9fd5063452ab54e90deae287793d7e4e0031dca682df1732c2ee4183fccc602da3be02be4e8fb00cc3196331399a4ac28ddd7421e616c85e0f12a225b21bb28f6da16c81dc0ab09bfeb6109f7e6cd7c96a142ba70b88df549d9e42d33e82c34c67b1b5; jrose=3E5425EE1B4F335D3C335015B3905C41.mooc-3203569194-vjzf8; tl=1; videojs_id=2449896'}

    url = 'https://mooc1-1.chaoxing.com/bbscircle/addreply'

    data = 'clazzid=33808600&topicId=242890550&content={}&type=6&files=&cpi=156496937&ut=s&attachmentFile=&openc=&showChooseClazzId=list_33808600'

    api = 'https://api.ly522.com/yan.php?format=json'

    for i in range(1000):
        yiyan = get(api).json()
        print(yiyan)
        resp = post(url, headers=headers, data=data.format(quote(yiyan['text'])))
        # print(resp.text)


if __name__ == '__main__':
    from threading import Thread

    threads = []
    for _ in range(50):
        t = Thread(target=main)
        threads.append(t)
        t.start()
