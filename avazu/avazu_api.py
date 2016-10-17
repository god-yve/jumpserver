#-*- coding:utf-8 -*-
from jumpserver.api import *
from juser.models import User
from juser.user_api import *
from jperm.perm_api import get_role_push_host
from datetime import datetime
from jumpserver.api import logger

def add_register_user(register_user):
    """
    创建用户账号
    """
    logger.debug("进入工具函数: 'add_register_user'")
    # 用户姓名
    name = register_user.name
    # 注册账号名及密码
    username = register_user.username
    password = register_user.password
    email = register_user.email
    # 自动生成用户UUID及SSH密钥
    uuid_r = uuid.uuid4().get_hex()
    ssh_key_pwd = PyCrypt.gen_rand_pass(16)
    # 默认用户不加入任何组
    groups = [ ]
    admin_groups = []
    # 用户默认为普通用户
    role = 'CU'
    # 默认激活用户账号
    is_active = 1

    try:
        # 创建jumpserver的User对象
        user =  db_add_user(username=username, name=name,
                                   password=password,
                                   email=email, role=role, uuid=uuid_r,
                                   groups=groups, admin_groups=admin_groups,
                                   ssh_key_pwd=ssh_key_pwd,
                                   is_active=is_active,
                                   date_joined=datetime.now())
        logger.debug("jumpserver用户添加成功: %s", user.username)
        # 在堡垒机上添加jumpserver用户对应的操作系统账号
        server_add_user(username=username, ssh_key_pwd=ssh_key_pwd)
        logger.debug("操作系统账号添加成功: %s", user.username )

    except ServerError,e:
        logger.debug(u'jumpserver用户账号添加失败: %s' %  username)
        raise ServerError
    # 更新注册用户状态为已处理
    register_user.is_added = 1
    register_user.save()
    logger.debug(u'%s :注册用户状态更为为以处理' % (register_user.name))
    try: 
        user_add_mail(user, kwargs={'password': password  , 'ssh_key_pwd': user.ssh_key_pwd})
    except:
        logger.debug("ERROR: 发送邮件失败")
        return "ERROR: 发送邮件失败"
    logger.debug(u'用户"%s"邮件通知已发送' % (user.username))
    return u'添加用户"%s"成功!\n' % (register_user.username)


