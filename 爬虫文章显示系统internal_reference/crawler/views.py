from django.shortcuts import render, redirect, get_object_or_404  
from django.contrib.auth import authenticate, login, logout  
from django.core.paginator import Paginator  
from .models import CrawlerData  
from django.db.models import Q  

def user_login(request):  
    if request.method == 'POST':  
        username = request.POST['username']  
        password = request.POST['password']  
        user = authenticate(request, username=username, password=password)  
        if user is not None:  
            login(request, user)  
            return redirect('data_list')  
    return render(request, 'login.html')  

def user_logout(request):  
    logout(request)  
    return redirect('user_login')  

def data_list(request):  
    query = request.GET.get('search', '')  
    if query:  
        keywords = query.split()  # 将查询字符串分割成多个关键词  
        query_filter = Q()  

        # 为每个关键词添加查询条件  
        for keyword in keywords:  
            query_filter |= Q(keyword__icontains=keyword)  # 使用或条件  

        # 执行查询并去重  
        data = CrawlerData.objects.filter(query_filter).distinct() 
    else:  
        data = CrawlerData.objects.all()  

    paginator = Paginator(data, 10)  # 每页显示 10 条数据  
    page_number = request.GET.get('page')  
    page_obj = paginator.get_page(page_number)  

    return render(request, 'data_list.html', {'page_obj': page_obj, 'query': query})  

# 新增视图函数以显示新闻详细信息  
def news_detail(request, id):  
    news = get_object_or_404(CrawlerData, id=id)  
    return render(request, 'news_detail.html', {'news': news})