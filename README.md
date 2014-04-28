# 珠三角技术沙龙网站工程

欢迎开发者参与到沙龙网站的开发工作中来。

参与官方网站的童鞋，请在github上fork：https://github.com/gztechparty/techparty/ 这个仓库到自己帐号上，提交代码采用pull request的方式来完成。

开发环境要求：

- 操作系统随意
- python2.6以上
- virtualEnv看开发者习惯，建议使用。

代码风格要求：

- 严格按照PEP8标准，提交前建议使用pyflake.py检查语法错误及pep8兼容性。
- 不import多余的lib。
- 尽量不要from moudle import *
- 命令规则不多讲了吧？类名首字母大写，函数就小写即可，长名字使用下划线连接。

### 复制代码本到地

`git clone git@github.com:gztechparty/techparty.git`

这个地址你fork了之后要换回自己的哇。

### 安装依赖

如果习惯使用virtualEnv的就顺手创建一个techparty的虚拟环境吧。

切换至techpary项目根目录下（有manage.py那个文件的）执行下面命令：

`sudo pip install -r requirements.txt`

会为本地的python安装上项目需要的依赖。

### 生成数据库

留在上一步的目录中，执行syncdb命令：

`python manage.py syncdb`

该命令会询问是否创建一个管理员用户，按指示操作创建一个呗。

对了，默认情况下会使用sqlite做这数据库的backend，如果你在本地开发想要使用到mysql或其他，请在xsettings.py文件中替换DATABASE的配置信息。其他配置信息也可以在xsettings.py中覆盖。

再对了，已经启用了south，往后大家如果需要更改model的字段，请先用`python manage.py schemamigration appname --auto`来生成差异文件，再`python manage.py migrate appname`应用到数据库。

### 运行

`python manage.py runserver`

修改端口,监听地址运行:

`python manage.py runserver 0.0.0.0:5000`


如果没有报错，整个系统运行起来了，这时候访问：http://localhost:8000/admin/ 可以看到管理界面。用刚才创建的管理员帐号登录进去吧。
