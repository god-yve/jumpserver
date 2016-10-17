#-*- coding:utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import render_to_response, render
from jasset.models import Asset
from jumpserver.api import require_role, my_render
from avazu.models import RegisterUser, ApplyHosts
from avazu.avazu_api import add_register_user
from datetime import datetime, timedelta
from jumpserver.api import logger
from juser.models import User
from jasset.models import Asset


# Create your views here.

def user_signup(request):
    u"""
    保存注册用户信息
    将所有注册用户信息保存在单独一张表中等待处理
    
    """
    error = ''
    msg = ''
    jump_run_log = open('/tmp/jumpserver.log', 'w+')
    jump_run_log.write("调用函数: add_registered_user\n")
    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email')
        expire = int(request.POST.get('expire'))
        password = request.POST.get('password')

        # 所有字段不能为空
        if all((username, name, email, password, expire)):
            # 检查用户名是否已经存在
            if len(RegisterUser.objects.filter(username=username)) == 0:
                try:
                    # 调用api接口创建用户账号
                    new_user = RegisterUser(username=username, name=name, email=email, password=password, expire=expire)
                    new_user.save()
                except Exception, e:
                    error = u'ERROR: 服务器错误: ' + str(e)
                else:
                   msg = u'OK: 您的申请已提交, 请耐心等待邮件'
            else:
                error = u'ERROR: 用户名已存在, 请重新输入'
        else:
            error = u'ERROR: 信息不能为空, 请重新填写'
    return render_to_response('avazu/user_register.html', locals())



@require_role(role='super')
def list_registered_user(request):
    u"""
    列出所有等待处理的注册用户及主机申请记录信息
    
    """
    registered_users = RegisterUser.objects.filter(is_added=0)
    applyhosts = ApplyHosts.objects.filter(is_added=0) 
    return my_render('avazu/list_registered_user.html', locals(), request)


@require_role(role='super')
def add_register(request):
    """
    为注册用户生成jumpserver账号

    """
    jump_run_log = open('/tmp/jumpserver.log', 'w')
    if request.method == 'GET':
        uid = request.GET.get('id','')
        print >>jump_run_log, "%s -- GET(add) uid: %s" % (datetime.now(), uid)
        new_user = RegisterUser.objects.get(id=uid)
        msg = add_register_user(new_user)
        return HttpResponse(msg)
    else:
        return HttpResponse('improssable!')


@require_role(role='super')
def del_register(request):
    """
    删除注册信息
    不同意用户的注册申请

    """
    logger.debug("开始删除注册记录, 执行函数: del_register")
    if request.method == "GET":
        user_ids = request.GET.get('id', '')
        logger.debug("%s -- GET del uids: %s" % (datetime.now(),user_ids))
        user_id_list = user_ids.split(',')
    elif request.method == "POST":
        user_ids = request.POST.get('id', '')
        looger.debug("%s -- POST del uids: %s" % (datetime.now(), user_ids))
        user_id_list = user_ids.split(',')
    else:
        logger.debug("%s -- 非GET, 也不是POST请求无法处理的错误" % datetime.now())
        return HttpResponse('错误请求')
    for user_id in user_id_list:
        try:
            user = RegisterUser.objects.get(id=int(user_id))
            logger.debug("%s -- del user: %s" % (datetime.now(), user.name))
        except:
            return HttpResponse(u'error')
        else:
            if user and user.username != 'admin':
                user.delete()
                logger.debug(u"删除注册记录:%s(%s) " % (user.name, user.username))
                return HttpResponse(u'删除成功')
                                            

@require_role(role='user')
def asset_apply(request):
    error = ""
    msg = "" 
    # 取得登陆用户的ID
    uid = request.user.id
    # 取得用户ID对应的User对象
    user = User.objects.get(id=uid)
    # 通过User对象获取用户所有的授权规则
    rule = user.perm_rule.all()[0]
    # 所有主机
    assets = Asset.objects.all()
    asset_appled = []
    
    if request.method == "POST": 
        asset_selected = request.POST.getlist('asset')   
        if asset_selected == []: 
            error = "请至少选择一台主机"
        else: 
            for asset_id in asset_selected:
                asset = Asset.objects.get(id=asset_id)
                if asset not in rule.asset.all():
                    msg = msg + asset.ip + " "  

            if msg != "":
                new_apply = ApplyHosts(username=user.username, hosts=msg,is_added=0)
                new_apply.save()
                msg = "申请已受理, 请耐心等待!"
                
    return render(request, 'avazu/asset_apply.html', locals())
    






@require_role(role='super')
def add_applyhost(request):
    u'''
     处理主机申请
     点击"同意添加"按钮后将更新用户的授权规则, 添加主机授权给用户

     '''
    jump_run_log = open('/tmp/jumpserver.log', 'w+')
    jump_run_log.write("%s - 调用函数: del_applyhost\n" % datetime.now())
    if request.method == "GET":
        # 取得记录在表中的ID
        apply_id = request.GET.get('id')
        jump_run_log.write('%s - 操作的记录ID是: %s\n' % (datetime.now(), apply_id))
        new_apply = ApplyHosts.objects.get(id=int(apply_id))
        jump_run_log.write('%s - 操作的记录内容是: %s, %s, %s\n' % (
                    datetime.now(), new_apply.id, new_apply.username, new_apply.hosts))
        # 根据username取得User对象 
        apply_user = User.objects.get(username=new_apply.username)
        jump_run_log.write('%s - 对应的用户是(id,username):%s, %s\n' % (
                          datetime.now(), apply_user.id, apply_user.username))
        # 从User对象上取出用户所有授权规则(PermRule)
        rule_collections = apply_user.perm_rule.all()
        # 假设用户只有一个授权规则
        rule = rule_collections[0]
        jump_run_log.write('%s - 用户对应的授权规则是: %s\n' % (datetime.now(), rule.name))
        # 申请授权的主机IP列表
        hosts_ip = new_apply.hosts.split()
         
        # 检查每一个申请的主机是否已经存在于授权规则
        # 如果没有则将主机添加到授权, 否则就跳过
        for ip in hosts_ip:
            # 取得IP对应的Asset对象
            asset = Asset.objects.get(ip=ip)
            # 检查规则中是否已经存在主机
            # 没有则添加
            if asset not in rule.asset.all():
                 rule.asset.add(asset)
                 jump_run_log.write('%s - 添加主机(规则, 主机):%s, %s\n' % (
                                  datetime.now(), rule.name, asset.ip))
         
                   
 
        jump_run_log.write("%s - 所有主机都已添加完成" % (datetime.now())) 
        # 将记录标记为已处理, 并更新记录状态
        new_apply.is_added = 1
        new_apply.save()
        jump_run_log.write("%s - 主机申请记录更新为已处理" % (datetime.now())) 
        return HttpResponse('OK: 主机以添加成功')

    elif request.method == "POST":
        # 取得记录在表中的ID
        apply_id = request.GET.get('id')
    
    else:
         return HttpResponse("ERROR: 不可能除GET和POST之外的其它方法!")

    return HttpResponse("OK: 主机授权已更新")


@require_role(role='super')
def del_applyhost(request):
    jump_run_log = open('/tmp/jumpserver.log', 'w+')
    jump_run_log.write("调用函数: del_applyhost\n")
    if request.method == "GET":
        ids = request.GET.get('id', '')
        print >>jump_run_log, "%s -- GET 删除主机申请记录ID: %s\n" % (datetime.now(),ids)
        id_list = ids.split(',')
        print >>jump_run_log, "%s -- 删除记录ID列表: %s\n" % (datetime.now(),id_list)

    elif request.method == "POST":
        ids = request.POST.get('id', '')
        print >>jump_run_log, "%s -- POST 删除主机申请记录ID: %s\n" % (datetime.now(), ids)
        id_list = ids.split(',')
        print >>jump_run_log, "%s -- 删除记录ID列表: %s\n" % (datetime.now(),id_list)
    else:
        print >>jump_run_log, "%s -- 非GET, 也不是POST请求无法处理的错误\n" % datetime.now()
        return HttpResponse('错误请求')

    print >>jump_run_log, "%s -- 准备进入for循环" % datetime.now()
    for id in id_list:
        print >>jump_run_log, "%s -- 进入到for循环" % datetime.now()
        try:
            applyhost = ApplyHosts.objects.get(id=int(id))
            print >>jump_run_log, "%s -- 删除主机申请记录: %s, %s\n" % (datetime.now(), applyhost.username, applyhost.hosts)
        except:
            print >>jump_run_log, "获取记录信息失败\n"
            return HttpResponse(u'error:无法获取申请记录信息')

        try:
            applyhost.delete()
            print >>jump_run_log, "%s -- %s: %s 主机申请记录成功删除\n" % (datetime.now(), applyhost.username, applyhost.hosts)
        except:
            print >>jump_run_log, "%s -- 调用delete()失败\n" % datetime.now()
            return HttpResponse(u'error: 删除失败')
          
        return HttpResponse(u'删除成功')

