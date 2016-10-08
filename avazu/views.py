#-*- coding:utf-8 -*-
from django.shortcuts import render_to_response, render
from jasset.models import Asset

# Create your views here.

def add_registered_user(request):
    error = ''
    msg = ''
    hosts = Asset.objects.all()
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


