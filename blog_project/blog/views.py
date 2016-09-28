import pdb
import logging
from django.shortcuts import render,redirect
from django.conf import settings
from blog.models import *
from django.core.paginator import Paginator,InvalidPage,EmptyPage,PageNotAnInteger
from django.db import connection
from django.db.models import Count
from blog.forms import *
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.hashers import make_password
# Create your views here.
logger=logging.getLogger('blog.views')
def global_setting(request):
    # 导航分类数据的获取
    SITE_NAME=settings.SITE_NAME
    SITE_DESC=settings.SITE_DESC
    category_list = Category.objects.all()
    archive_list = Article.objects.distinct_date()
    #pdb.set_trace()
    print("start")
    #广告数据
    #标签云数据
    tag_list=Tag.objects.all()
    #友情连接
    link_list=Links.objects.all()
    #文章排行榜
    #评论排行
    comment_count_list=Comment.objects.comment_list()
    article_comment_list=[Article.objects.get(pk=comment['article']) for comment in comment_count_list]
    #浏览量排行
    article_click_list = Article.objects.click_count()
    #站长推荐
    article_recomment=Article.objects.recommend()
    return locals()

def index(request):
    try:

        #获取文章数据
        article_list=Article.objects.all()
        article_list=getPage(request,article_list)
    except Exception as e:
        logger.error(e)
    return render(request, 'index.html', locals())

#文章详情页面
def article(request):
    try:
       #获取文章id
       id=request.GET.get('id',None)
       try:
           #获取文章信息
            article=Article.objects.get(pk=id)
       except Article.DoesNotExist:
            return render(request,'failure.html',{'reason':'没有找到对应的文章'})

            # 评论表单

       comment_form = CommentForm({'author': request.user.username,
                                   'email': request.user.email,
                                   'url': request.user.url,
                                   'article': id} if request.user.is_authenticated() else{'article': id})
       #request.user.is_authenticated()判断用户是否已登录？
       #request.user代表当前登录的用户
       # 获取所有的评论信息
       comments = Comment.objects.filter(article=article).order_by('id')
       #降所有的评论信息分为2大类
       #一类是没有父级评论的放在comment_list列表里
       #二类是有父级评论的放在comment_list2列表里
       comment_list = []
       comment_list2=[]
       for comment in comments:
           if comment.pid is None:
               comment_list.append(comment)
           else:
               comment_list2.append(comment)
       #对于comment_list里的评论数据，可能有子评论数据也可能没有子评论
       for item in comment_list:
           #没有子评论的就不管
           if not hasattr(item, 'children_comment'):
               setattr(item, 'children_comment', [])
            #有子评论的数据就添加子评论
           for comment in comments:
               if comment.pid == item:
                   item.children_comment.append(comment)
                   break
       for item in comment_list2:
           if not hasattr(item, 'children_comment'):
               setattr(item, 'children_comment', [])
           for comment in comments:
               if comment.pid == item:
                   item.children_comment.append(comment)
                   comment_list.append(item)

    except Exception as e:
        logger.error(e)
    return render(request, 'article.html', locals())

def archive(request):
    try:
        year=request.GET.get('year',None)
        month=request.GET.get('month',None)
        article_list = Article.objects.filter(date_publish__icontains=year+'-'+month)
        article_list=getPage(request,article_list)
    except Exception as e:
        logger.error(e)
    return render(request, 'archive.html', locals())



#分页代码的封装
def getPage(request,article_list):
    paginator = Paginator(article_list, 3)
    try:
        page = int(request.GET.get('page', 1))
        article_list = paginator.page(page)#接受分页的数据保存到article_list
    except (EmptyPage, InvalidPage, PageNotAnInteger):
        article_list = paginator.page(1)
    return article_list
# 提交评论
def comment_post(request):
    try:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            #获取表单信息
            comment = Comment.objects.create(username=comment_form.cleaned_data["author"],
                                             email=comment_form.cleaned_data["email"],
                                             url=comment_form.cleaned_data["url"],
                                             content=comment_form.cleaned_data["comment"],
                                             article_id=comment_form.cleaned_data["article"],
                                             user=request.user if request.user.is_authenticated() else None)
            comment.save()
        else:
            return render(request, 'failure.html', {'reason': comment_form.errors})
    except Exception as e:
        logger.error(e)
    return redirect(request.META['HTTP_REFERER'])
# 注销
def do_logout(request):
    try:
        logout(request) #调用django提供的logout方法
    except Exception as e:
        logger.error(e)
    return redirect(request.META['HTTP_REFERER'])


# 注册
def do_reg(request):
    try:
        if request.method == 'POST':
            reg_form = RegForm(request.POST)
            if reg_form.is_valid():
                # 注册
                user = User.objects.create(username=reg_form.cleaned_data["username"],
                                    email=reg_form.cleaned_data["email"],
                                    url=reg_form.cleaned_data["url"],
                                    password=make_password(reg_form.cleaned_data["password"]),)
                user.save()

                # 登录
                user.backend = 'django.contrib.auth.backends.ModelBackend' # 指定默认的登录验证方式
                login(request, user) #登录调用login方法，login方法为python标准库提供的方法
                return redirect(request.POST.get('source_url'))#前端页面隐藏域页面来源的地址
            else:
                return render(request, 'failure.html', {'reason': reg_form.errors})
        else:
            reg_form = RegForm()
    except Exception as e:
        logger.error(e)
    return render(request, 'reg.html', locals())


# 登录
def do_login(request):
    #pdb.set_trace()
    try:
        if request.method == 'POST':
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                # 登录
                username = login_form.cleaned_data["username"]
                password = login_form.cleaned_data["password"]
                user = authenticate(username=username, password=password)#使用django提供的验证方法
                #返回user对象
                if user is not None:
                    user.backend = 'django.contrib.auth.backends.ModelBackend' # 指定默认的登录验证方式
                    login(request, user)
                else:
                    return render(request, 'failure.html', {'reason': '登录验证失败'})
                return redirect(request.POST.get('source_url'))
            else:
                return render(request, 'failure.html', {'reason': login_form.errors})
        else:
            login_form = LoginForm()#以GET方法提交访问的登录页面
    except Exception as e:
        logger.error(e)
    return render(request, 'login.html', locals())

def category(request):
    try:
        #获取分类的id号
        cid=request.GET.get('cid',None)
        #根据分类的id号找到对应的文章
        try:
            category=Category.objects.get(pk=cid)
        except Category.DoesNotExist:
            return render(request, 'failure.html', {'reason': "该分类不存在"})
        article_list = Article.objects.filter(category=category)
        article_list = getPage(request, article_list)
    except Exception as e :
        logger.error(e)
    return render(request,'category.html',locals())

def tag(request):
    try:
        #获取标签id号
        cid=request.GET.get('cid',None)
        try:
            #根据id号获取标签对象
            tag=Tag.objects.get(pk=cid)
        except Tag.DoesNotExist:
            return render(request, 'failure.html', {'reason': "该标签不存在"})
        article_list=Article.objects.filter(tag=tag)
        article_list=getPage(request,article_list)
    except Exception as e:
        logger.error(e)
    return render(request,'tag.html',locals())
