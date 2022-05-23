from functools import partial
from typing import Union
from django.urls import URLPattern, URLResolver, path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views

from restapi.views import UserViewSet, CategoryViewSet, GroupViewSet, ExpensesViewSet, \
    index, logout, balance, logProcessor


router: DefaultRouter = DefaultRouter()
router.register('users', UserViewSet)
router.register('categories', CategoryViewSet)
router.register('groups', GroupViewSet)
router.register('expenses', ExpensesViewSet)

urlpatterns: list[Union[URLResolver, URLPattern]] = [
    path('', index, name='index'),
    path('auth/logout/', logout),
    path('auth/login/', views.obtain_auth_token),
    path('balances/', balance),
    path('process-logs/', logProcessor)
]

urlpatterns += router.urls
