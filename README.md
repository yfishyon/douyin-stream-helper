\# Douyin Stream Helper



一个基于python的直播推流助手,通过拦截直播伴侣创建直播接口获取rtmp地址,并可直接推送到obs 仅支持window系统



---



\## 特性



\- 自动获取直播伴侣直播推流地址

\- 可直接推送到obs并开启直播

\- 自动解决推流冲突





\## 安装依赖



```bash

pip install -r requirements.txt

```



---



\## 配置



1\. 修改obs配置 (在main.py里)：



```python

obs\_HOST = "127.0.0.1"

obs\_PORT = 4455

obs\_PASSWORD = ""

```

(如果直接用可执行文件的话就只能用默认的设置)



2\. 默认保存证书和配置在用户目录：



```

~/.douyin\_stream/

```



---



\## 运行



直接运行 `main.py`：



```bash

python main.py

```



程序会：



1\. 检查管理员权限,如果没有,会自动重新以管理员模式启动

2\. 自动获取推流信息并推送到obs并开启直播

3\. 自动解决推流冲突



---



\## 打包



\### 使用Nuitka



```bash

nuitka --standalone --onefile --windows-uac-admin --output-dir=nuitka\_out --output-filename=douyin-rtmp-nuitka.exe main.py

```



\### 使用PyInstaller



```bash

pyinstaller --onefile --uac-admin main.py

```



打包后生成的可执行文件可以直接双击运行,无需完整python环境



---



\## 注意事项



\- 推流失败时,请检查 obs WebSocket 是否开启,以及端口和密码配置是否正确。



---



\## 项目结构



```

.

├─ main.py            #主程序

├─ certmgr.py         #证书管理

├─ hostmgr.py         #host管理

├─ obs.py             #obs推流控制

├─ requirements.txt   #依赖

└─

