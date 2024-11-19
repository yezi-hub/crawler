from django.urls import path  
from .views import user_login, user_logout, data_list , news_detail

urlpatterns = [  
    path('login/', user_login, name='user_login'),  
    path('logout/', user_logout, name='user_logout'),  
    path('data/', data_list, name='data_list'),  
    path('data/<int:id>/', news_detail, name='news_detail'),  # 详细信息路径  
]