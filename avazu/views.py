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

def add_registered_user(request):
    u"""
    显示并处理用户注册
    """
    error = ''
    msg = ''
    hosts = Asset.objects.all()
    jump_run_log = open('/tmp/jumpserver.log', 'w+')
    jump_run_log.write("调用函数: add_registered_user\n")
    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email')
        expire_date = datetime.now() + timedelta(hours=int(request.POST.get('expire')))
        password = request.POST.get('password')
        host_id_list = request.POST.getlist('hosts')
        hosts = ''
        for  host_id in host_id_list:
            hosts = hosts + host_id + ' '

        if all((username, name, email, password, hosts, expire_date)):
            if len(RegisterUser.objects.filter(username=username)) == 0:
                try:
                    new_user = RegisterUser(username=username, name=name, email=email, password=password, hosts=hosts, expire_date=expire_date)
                    new_user.save()
                except Exception, e:
                    error = u'无法连接数据库: ' + str(e)
                else:
                   msg = u'您的申请已提交, 请耐心等待'
            else:
                error = u'用户名已存在, 请重新输入'
        else:
            error = u'信息不能为空, 请重新填写'
    return render_to_response('avazu/user_register.html', locals())



@require_role(role='super')
def list_registered_user(request):
    u"""
    列出所有等待处理的注册用户信息
    """
    registered_users = RegisterUser.objects.filter(is_added=0)
    applyhosts = ApplyHosts.objects.filter(is_added=0) 
    return my_render('avazu/list_registered_user.html', locals(), request)


@require_role(role='super')
def add_register(request):
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
    jump_run_log = open('/tmp/jumpserver.log', 'w+')
    jump_run_log.write("调用函数: del_register\n")
    print >>jump_run_log, "调用函数: del_register\n" 
    if request.method == "GET":
        user_ids = request.GET.get('id', '')
        print >>jump_run_log, "%s -- GET del uids: %s" % (datetime.now(),user_ids)
        user_id_list = user_ids.split(',')
    elif request.method == "POST":
        user_ids = request.POST.get('id', '')
        print >>jump_run_log, "%s -- POST del uids: %s" % (datetime.now(), user_ids)
        user_id_list = user_ids.split(',')
    else:
        print >>jump_run_log, "%s -- 非GET, 也不是POST请求无法处理的错误" % datetime.now()
        return HttpResponse('错误请求')
    for user_id in user_id_list:
        try:
            user = RegisterUser.objects.get(id=int(user_id))
            print >>jump_run_log, "%s -- del user: %s" % (datetime.now(), user.name)
        except:
            return HttpResponse(u'error')
        else:
            if user and user.username != 'admin':
                logger.debug(u"删除注册用户 %s " % user.username)
                user.delete()
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
    pass



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

