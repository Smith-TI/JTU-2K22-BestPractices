# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from decimal import Decimal
import logging
from time import time

from django.http import HttpResponse
from django.contrib.auth.models import User

# Create your views here.
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, action, authentication_classes, permission_classes
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from restapi.serializers import CategorySerializer, Expenses, ExpensesSerializer, Groups, GroupSerializer, UserExpense, UserSerializer, Category
from restapi.custom_exception import UnauthorizedUserException
from django.db.models import QuerySet

from restapi.utils import aggregate_logs, clean_up_logs, multiThreadedReader, normalize, response_format, sort_logs_by_time_stamp


def index(_request) -> HttpResponse:
    '''Handle the base route'''
    return HttpResponse("Hello, world. You're at Rest.")


@api_view(['POST'])
def logout(request) -> Response:
    '''Log a User out'''
    if not 'user' in request:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data="field `user` missing in request")
    if not 'auth_token' in request.user:
        return Response(status=status.HTTP_401_UNAUTHORIZED,
                        data="Auth Token missing in request")
    request.user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def balance(request) -> Response:
    '''Get the balance for a user'''

    if not 'user' in request:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data="field `user` missing in request")
    user = request.user

    starttime = int(time.time() * 1000.0)
    logging.info(f"Calculating balance for {user}")
    expenses = Expenses.objects.filter(users__in=user.expenses.all())
    final_balance = {}
    for expense in expenses:
        expense_balances = normalize(expense)
        for eb in expense_balances:
            from_user = eb['from_user']
            to_user = eb['to_user']
            if from_user == user.id:
                final_balance[to_user] = final_balance.get(
                    to_user, 0) - eb['amount']
            if to_user == user.id:
                final_balance[from_user] = final_balance.get(
                    from_user, 0) + eb['amount']
    final_balance = {k: v for k, v in final_balance.items() if v != 0}

    response = [{"user": k, "amount": int(v)}
                for k, v in final_balance.items()]
    endtime = int(time.time() * 1000.0)
    logging.info(f'Calculated balance in {endtime - starttime}ms')
    return Response(response, status=200)


class user_view_set(ModelViewSet):
    '''View Set for a User'''
    queryset: QuerySet = User.objects.all()
    serializer_class: UserSerializer = UserSerializer
    permission_classes: tuple = (AllowAny,)


class category_view_set(ModelViewSet):
    '''View Set for a Category'''
    queryset: QuerySet = Category.objects.all()
    serializer_class: CategorySerializer = CategorySerializer
    http_method_names: list[str] = ['get', 'post']


class group_view_set(ModelViewSet):
    '''View Set for a Group'''
    queryset: QuerySet = Groups.objects.all()
    serializer_class: GroupSerializer = GroupSerializer

    def get_queryset(self):
        '''Returns the queryset for a User'''
        if not self.request.user:
            raise ValueError("field `user` missing in request")
        user = self.request.user
        groups = user.members.all()
        if self.request.query_params.get('q', None) is not None:
            groups = groups.filter(
                name__icontains=self.request.query_params.get('q', None))
        return groups

    def create(self) -> Response:
        '''Creates a group, adds a user to it and then save it'''
        if not self.request.user:
            raise ValueError("field `user` missing in request")
        user = self.request.user
        data = self.request.data
        group = Groups(**data)
        group.save()
        group.members.add(user)
        serializer = self.get_serializer(group)
        return Response(serializer.data, status=201)

    @action(methods=['put'], detail=True)
    def members(self, request, pk=None) -> Response:
        '''Handle PUT method on members'''
        group = Groups.objects.get(id=pk)
        if group not in self.get_queryset():
            raise UnauthorizedUserException()
        body = request.data
        if body.get('add', None) is not None and body['add'].get('user_ids', None) is not None:
            added_ids = body['add']['user_ids']
            for user_id in added_ids:
                group.members.add(user_id)
        if body.get('remove', None) is not None and body['remove'].get('user_ids', None) is not None:
            removed_ids = body['remove']['user_ids']
            for user_id in removed_ids:
                group.members.remove(user_id)
        group.save()
        return Response(status=204)

    @action(methods=['get'], detail=True)
    def expenses(self, pk=None) -> Response:
        '''Handle GET method on expense'''
        group = Groups.objects.get(id=pk)
        if group not in self.get_queryset():
            raise UnauthorizedUserException()
        expenses = group.expenses_set
        serializer = ExpensesSerializer(expenses, many=True)
        return Response(serializer.data, status=200)

    @action(methods=['get'], detail=True)
    def balances(self, pk=None) -> Response:
        '''Handle GET method on balances'''
        starttime = int(time.time() * 1000.0)
        logging.info(f"Getting balance for Group with id: {pk}")
        group = Groups.objects.get(id=pk)
        if group not in self.get_queryset():
            raise UnauthorizedUserException()
        expenses = Expenses.objects.filter(group=group)
        dues = {}
        for expense in expenses:
            user_balances = UserExpense.objects.filter(expense=expense)
            for user_balance in user_balances:
                dues[user_balance.user] = dues.get(user_balance.user, 0) + user_balance.amount_lent \
                    - user_balance.amount_owed
        dues = [(k, v)
                for k, v in sorted(dues.items(), key=lambda item: item[1])]
        start = 0
        end = len(dues) - 1
        balances = []
        while start < end:
            amount = min(abs(dues[start][1]), abs(dues[end][1]))
            amount = Decimal(amount).quantize(Decimal(10)**-2)
            user_balance = {
                "from_user": dues[start][0].id, "to_user": dues[end][0].id, "amount": str(amount)}
            balances.append(user_balance)
            dues[start] = (dues[start][0], dues[start][1] + amount)
            dues[end] = (dues[end][0], dues[end][1] - amount)
            if dues[start][1] == 0:
                start += 1
            else:
                end -= 1
        endtime = int(time.time() * 1000.0)
        logging.info(
            f"Calculated balance for Group with id: {pk} in {endtime - starttime}ms")
        return Response(balances, status=200)


class expenses_view_set(ModelViewSet):
    '''View Set for Expense'''
    queryset: QuerySet = Expenses.objects.all()
    serializer_class: ExpensesSerializer = ExpensesSerializer

    def get_queryset(self):
        '''Returns the queryset for Expenses'''
        if not 'user' in self.request:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data="field `user` missing in request")
        user = self.request.user
        if self.request.query_params.get('q', None) is not None:
            expenses = Expenses.objects.filter(users__in=user.expenses.all())\
                .filter(description__icontains=self.request.query_params.get('q', None))
        else:
            expenses = Expenses.objects.filter(users__in=user.expenses.all())
        return expenses


@api_view(['post'])
@authentication_classes([])
@permission_classes([])
def logProcessor(request) -> Response:
    '''Handle POST method on processing log files'''
    starttime = int(time.time() * 1000.0)

    if not 'data' in request:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={"status": "failure", "reason": "field `data` missing in request"})
    data = request.data
    num_threads = data['parallelFileProcessingCount']
    log_files = data['logFiles']
    logging.info(
        f'starting log processor with {num_threads} threads and {len(log_files)} log files')
    if num_threads <= 0 or num_threads > 30:
        logging.error('Parallel Processing Count out of expected bounds')
        return Response({"status": "failure", "reason": "Parallel Processing Count out of expected bounds"},
                        status=status.HTTP_400_BAD_REQUEST)
    if len(log_files) == 0:
        logging.error('No log files provided in request')
        return Response({"status": "failure", "reason": "No log files provided in request"},
                        status=status.HTTP_400_BAD_REQUEST)
    logs = multiThreadedReader(
        urls=data['logFiles'], num_threads=data['parallelFileProcessingCount'])
    sorted_logs = sort_logs_by_time_stamp(logs)
    cleaned = clean_up_logs(sorted_logs)
    data = aggregate_logs(cleaned)
    response = response_format(data)
    endtime = int(time.time() * 1000.0)
    logging.info(f'Processed log files in {endtime - starttime}ms')
    return Response({"response": response}, status=status.HTTP_200_OK)
