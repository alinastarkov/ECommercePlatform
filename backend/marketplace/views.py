from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from rest_framework.views import APIView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import UserSerializer, UserSerializerWithToken, ItemSerializer, OrderSerializer, OrderedItemsSerializer
from .models import Item, Order
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
import uuid 
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.template.loader import render_to_string
from backend.settings import SECRET_KEY, DOMAIN, EMAIL_HOST_PASSWORD

@api_view(['GET'])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

#get all the items to display, if there is a current user then we exclude those items the users are selling
#else we display all the items
@api_view(['GET'])
@permission_classes((permissions.AllowAny, ))
def item_list(request):
    if 'username' in request.GET:
        username = request.GET['username']
        item = Item.objects.all().exclude(user__username=username)
    else:
        item = Item.objects.all()
    serializer = ItemSerializer(item, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes((permissions.AllowAny, ))
def get_all_users(request):
    all_users=User.objects.all()
    serializer = UserSerializer(all_users, many=True)
    return Response(serializer.data)
    
class UserList(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        serializer = UserSerializerWithToken(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ItemView(APIView):
    #todo: change to authentication token can access only
    permission_classes = (permissions.AllowAny,)
    def delete(self, request, format=None):
        item_name=request.data.get("item_name")
        Item.objects.get(name=item_name).delete()
        return HttpResponse("deleted!")

    def get(self, request, format=None):
        name=request.query_params.get("username")
        item = Item.objects.all().filter(user__username=name)
        serializer = ItemSerializer(item, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        parser_classes = (MultiPartParser, FormParser)
        #find the item with the same id to determine if its an update or not
        try:
            item_id = request.data.get('id')
            itemModel = Item.objects.get(id=item_id)
            img_field_req = request.data.get('image')
            #retrive the old image request if we user didnt upload new image
            if (img_field_req == "" or img_field_req == None):
                newData = request.data.copy()
                newData.update({"image": itemModel.image})
                serializer = ItemSerializer(itemModel, data=newData)
            else:
                #if there is an image field the update 
                serializer = ItemSerializer(itemModel, data=request.data)
        except (ObjectDoesNotExist, ValidationError, ValueError) as e:
            #if this is a new item then we simply create on in the db
            new_data = request.data.copy() # to make it mutable
            new_data['id'] = uuid.uuid4()
            serializer = ItemSerializer(data=new_data)
        #save 
        if serializer.is_valid():
            username = request.data.get("username")
            userInstance = User.objects.get(username=username)
            serializer.save(user = userInstance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print('error', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        #find the item list to update the inventory
        items_data = request.data.copy().pop('ordered_items')
        email = request.data.get('email')
        serializerOrder = OrderSerializer(data=request.data)
        if serializerOrder.is_valid():
            #update the inventory in the items
            for item_data in items_data:
                item = Item.objects.get(id=item_data['item_id'])
                new_inventory = item.inventory - item_data['quantity']
                serializerItem = ItemSerializer(item, data={'inventory': new_inventory}, partial=True)
                if serializerItem.is_valid():
                    serializerItem.save()
                    item_data.update({'name': item.name, 'brand': item.brand, 'size': item.size})
                else:
                    return Response(serializerItem.errors, status=status.HTTP_400_BAD_REQUEST)
             # save new order into the order db
            username = request.data.get("username")
            userInstance = User.objects.get(username=username)
            serializerOrder.save(user = userInstance)
            # context object for the email html template
            context = {
                'name': request.data.get('full_name'),
                'address': request.data.get('address'),
                'country': request.data.get('country'),
                'city': request.data.get('city'),
                'state': request.data.get('state'),
                'card': request.data.get('card_number'),
                'items_list': items_data, 
                'total': request.data.get('total_price')
            }
           # send email confirmation
            msg_html = render_to_string('email.html', context)
            message = Mail(from_email='hayleeluu@gmail.com', to_emails=[email],  subject='Order Confirmation', html_content=msg_html)
            try:
                sg = SendGridAPIClient('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')
                sg.send(message)
            except Exception as e:
                print(str(e))

            return Response(serializerOrder.data, status=status.HTTP_201_CREATED)
        return Response(serializerOrder.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, format=None):
        name=request.query_params.get("username")
        allOrders = Order.objects.filter(user__username=name)
        serializer = OrderSerializer(allOrders, many=True)
        return Response(serializer.data)
