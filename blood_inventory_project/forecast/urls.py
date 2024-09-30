from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_file, name='upload_file'),
    path('results/', views.results, name='results'),
    path('login_user', views.login_user, name="login"),
    path('logout/', views.logout_user, name='logout'),
    path('predefined-files/', views.predefined_file_list, name='predefined_file_list'),
    path('predefined-files/download/<str:filename>/', views.download_predefined_file, name='download_predefined_file'),
    path('predicted_demand/', views.predicted_demand, name='predicted_demand'),
    path('system_alerts/', views.notifications, name='notifications'),
    
]
