#-*- coding:utf-8 -*-

def add_register_user(register_user):
    # 姓名
    name = register_user.name
    # 账号名
    username = register_user.username
    password = register_user.password
    group = UserGroup(name='dev')
    email = register_user.email
    uuid_r = uuid.uuid4().get_hex()
    ssh_key_pwd = PyCrypt.gen_rand_pass(16)
    groups = [1]
    admin_groups = []
    # 普通用户
    role = 'CU'
    # 激活用户
    is_active = 1

    #
    error_log = open('/tmp/jumpserver.log', 'w')

    check_user_is_exist = User.objects.filter(username=username)
    if check_user_is_exist:
        error = u'用户 %s 已存在' % username
        raise ServerError
    try:
        # 向jumpserver user表添加注册用户
        user =  db_add_user(username=username, name=name,
                                   password=password,
                                   email=email, role=role, uuid=uuid_r,
                                   groups=groups, admin_groups=admin_groups,
                                   ssh_key_pwd=ssh_key_pwd,
                                   is_active=is_active,
                                   date_joined=datetime.datetime.now())
        # 在堡垒机上添加系统用户账号
        server_add_user(username=username, ssh_key_pwd=ssh_key_pwd)

        # 添加授权规则 
        # 获取所有 用户,用户组,资产,资产组,用户角色, 用于添加授权规则
        users = User.objects.all()                    # 所有用户列表
        assets = Asset.objects.all()                  # 所有主机列表
        asset_groups = AssetGroup.objects.all()       # 所有主机组列表
        # user_select = user.username                   # 需要授权的用户
        roles = PermRole.objects.all()                # 所有系统用户列表
    except ServerError,e:
        error = u'jumpserver用户账号添加失败: %s' %  username
        raise ServerError

    # 需要授权的用户信息
    #
    users_select = [user.id]                              # 需要授权多用户列表(用户ID)
    user_groups_select = [1]                               # 选中的用户组
    assets_select = register_user.hosts.split()           # 需要授权的主机列表(IP)
    assets_groups_select = []                             # 需要授权的主机组()
    roles_select = [1]                                    # 角色: admin
    rule_name = user.name                                 # 使用用户名作为授权规则名
    rule_comment = u'给' + name + u'的授权.'              # 规则说明

    try:
        # 查询已建立的授权中是否已经有同名规则
        # 
        rule = get_object(PermRule, name=rule_name)
        if rule:
            error_log.write(u'授权规则 %s 已存在\n' % rule_name)
            raise ServerError(u'授权规则 %s 已存在' % rule_name)

        # 授权规则名称及授权的系统用户账号不能为空
        # 
        if not all((rule_name, roles_select)):
            error_log.write(u'角色名称和规则名称不能为空')
            raise ServerError(u'角色名称和规则名称不能为空')

        # 获取需要授权的主机及主机组
        assets_obj = [Asset.objects.get(ip=ip) for ip in assets_select]
        error_log.write('需要授权的主机IP: %s\n' % assets_obj)
        # 需要授权的主机组, 此处不用对主机组授权因此为空
        asset_groups_obj = []

        # 所有授权主机组中的主机集合, 由于不对主机组授权所以为空
        group_assets_obj = []

        # 合并主机及主机组, 得到去重后的需要授权的主机列表
        #
        calc_assets = set(group_assets_obj) | set(assets_obj)
        error_log.write('需要授权主机集合:calc_assets: %s\n' % calc_assets)

        # 获取需要授权的用户列表
        users_obj = [User.objects.get(id=user_id) for user_id in users_select]
        user_groups_obj = [UserGroup.objects.get(id=user_gid) for user_gid in user_groups_select]
        error_log.write('需要授权的用户: %s\n' % users_obj)

        # 获取授予的角色列表
        roles_obj = [PermRole.objects.get(id=1)]
        error_log.write("roles_obj: %s\n" % roles_obj)
        need_push_asset = set()

        for role in roles_obj:
            asset_no_push = get_role_push_host(role=role)[1]  # 获取某角色已经推送的资产
            need_push_asset.update(set(calc_assets) & set(asset_no_push))
            if need_push_asset:
                error_log.write(u'没有推送系统用户 %s 的主机 %s'
                                  % (role.name, ','.join([asset.hostname for asset in need_push_asset])))
                raise ServerError(u'没有推送系统用户 %s 的主机 %s'
                                  % (role.name, ','.join([asset.hostname for asset in need_push_asset])))

        # 仅授权成功的，写回数据库(授权规则,用户,用户组,资产,资产组,用户角色)
        rule = PermRule(name=rule_name, comment=rule_comment)
        rule.save()
        rule.user = users_obj
        rule.user_group = user_groups_obj
        rule.asset = assets_obj
        rule.asset_group = asset_groups_obj
        rule.role = roles_obj
        rule.save()
    except ServerError, e:
        error_log.write(u'用户"%s"添加授权失败' % (register_user.name))
        error = u'用户"%s"添加授权失败' % (register_user.name)
        raise ServerError

    # 更新注册用户状态为已处理
    register_user.is_added = 1
    register_user.save()
    user_add_mail(user, kwargs=locals())
    return u'添加用户"%s"成功!' % (register_user.username)


