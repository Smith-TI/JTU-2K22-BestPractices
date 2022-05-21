from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import ValidationError
from django.contrib.auth.models import User

from restapi.models import Category, Groups, UserExpense, Expenses


class UserSerializer(ModelSerializer):
    '''Serializer for the User model'''

    def create(self, validated_data) -> User:
        '''Create a new user from the validated user data'''
        user: User = User.objects.create_user(**validated_data)
        return user

    class Meta(object):
        model: User = User
        fields: tuple[str] = ('id', 'username', 'password')
        extra_kwargs: dict[str, dict[str, bool]] = {
            'password': {'write_only': True}
        }


class CategorySerializer(ModelSerializer):
    '''Serializer for the Category model'''
    class Meta(object):
        model: Category = Category
        fields: str = '__all__'


class GroupSerializer(ModelSerializer):
    '''Serializer for the Group model'''
    members: UserSerializer = UserSerializer(many=True, required=False)

    class Meta(object):
        model: Groups = Groups
        fields: str = '__all__'


class UserExpenseSerializer(ModelSerializer):
    '''Serializer for the UserExpense model'''
    class Meta(object):
        model: UserExpense = UserExpense
        fields: list[str] = ['user', 'amount_owed', 'amount_lent']


class ExpensesSerializer(ModelSerializer):
    '''Serializer for the Expenses model'''
    users: UserExpenseSerializer = UserExpenseSerializer(
        many=True, required=True)

    def create(self, validated_data) -> Expenses:
        '''Create a new expense from the validated expense data'''
        expense_users = validated_data.pop('users')
        expense: Expenses = Expenses.objects.create(**validated_data)
        for eu in expense_users:
            UserExpense.objects.create(expense=expense, **eu)
        return expense

    def update(self, instance, validated_data):
        '''Update an expense instance to the validated expense data'''
        user_expenses = validated_data.pop('users')
        instance.description = validated_data['description']
        instance.category = validated_data['category']
        instance.group = validated_data.get('group', None)
        instance.total_amount = validated_data['total_amount']

        if user_expenses:
            instance.users.all().delete()
            UserExpense.objects.bulk_create(
                [
                    user_expense(expense=instance, **user_expense)
                    for user_expense in user_expenses
                ],
            )
        instance.save()
        return instance

    def validate(self, attrs):
        '''Validate an expense'''
        user_ids: list = [user['user'].id for user in attrs['users']]
        if len(set(user_ids)) != len(user_ids):
            raise ValidationError('Single user appears multiple times')
        return attrs

    class Meta(object):
        model: Expenses = Expenses
        fields: str = '__all__'
