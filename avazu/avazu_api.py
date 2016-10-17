#-*- coding:utf-8 -*-
from jumpserver.api import *
from juser.models import User
from jperm.models import PermRule, PermRole
from jasset.models import AssetGroup
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
        loggeo.debug(u'jumpserver用户账号添加失败: %s' %  username)
        raise ServerError

    # 开始为用户创建授权规则(PermRule)
    # 默认为每一个新注册用户创建一个与账号名相同的授权规则
    # 该授权中含有一个名为'zero'的资产组, 资产组中所包含的主机数量为0
    # 

    rule_name = user.username                         
    # 授权规则说明信息
    rule_comment = u'给(%s)的授权. 创建于: %s' %  (user.name, datetime.now())        # 授权规则说明
    # 创建一个授权规则对象, 随后更新授权信息
    new_rule = PermRule(name=rule_name, comment=rule_comment)
    new_rule.save()
    logger.debug("%s :授权规则对象创建成功" % new_rule.name)

    try:
        # 授权规则对应的用户
        rule_to_user = user
        logger.debug("规则对应的用户为 %s" % user.username)
        # 'zero'资产组
        # 默认每个注册用户都会被赋予'zero'资产组
        #
        asset_group = AssetGroup.objects.get(name = 'zero')            
        logger.debug("规则对应的资产组为: %s" % asset_group.name)
    except e:
        logger.debug("ERROR: 无法找到用户或资产组: %s" % e)
        return "ERROR: 更新授权规则失败"

    # 系统用户, 账号关联到的系统账号(jperm_permrole)
    # 1, admin
    # 2, dba
    # 默认使用: admin
    system_role = PermRole.objects.get(name="admin")
    logger.debug("规则对应的系统角色为: %s" % system_role.name)
    # 将授权规则与用户, 资产组, 系统角色相关联
    #
    new_rule.user.add(rule_to_user)
    new_rule.asset_group.add(asset_group)
    new_rule.role.add(system_role)
    try: 
        new_rule.save()
        logger.debug("%s :授权规则成功更新并保存" % new_rule.name) 
    except Exception, e:
        logger.debug("ERROR: 授权规则保存失败, %s" % e) 
        return "ERROR: 授权规则保存失败, %s" % e
        
 
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


