from django.db import models
from django.contrib.auth.models import User
import uuid 
from django.core.exceptions import ValidationError


# Create your models here.
def validate_content_message(content):
    if (content == ""or content == None or content.isspace()):
        raise ValidationError(
            'Content is empty or invalid',
            code = 'invalid',
            params = {
                'content' : content
            }
        )
class Item(models.Model):
    id = models.UUIDField(primary_key = True, default = uuid.uuid4, editable = False)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
    description = models.TextField()
    category = models.CharField(max_length=20)
    size = models.CharField(max_length=10)
    brand = models.CharField(max_length=20)
    price = models.PositiveSmallIntegerField(default=0)
    image = models.ImageField(upload_to='item_images/', null=True)
    inventory = models.PositiveSmallIntegerField(default=0)

class OrderedProducts(models.Model):
    id = models.UUIDField(primary_key = True, default = uuid.uuid4, editable = False)
    item_id = models.CharField(max_length=40)
    quantity = models.PositiveSmallIntegerField(default=0)
    price = models.PositiveSmallIntegerField(default=0)

class Order(models.Model):
    id = models.UUIDField(primary_key = True, default = uuid.uuid4, editable = False)
    user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=40, null=True)
    address = models.CharField(max_length=100)
    country = models.CharField(max_length=30)
    state = models.CharField(max_length=30)
    city = models.CharField(max_length=50)
    total_price = models.PositiveSmallIntegerField(default=0)
    card_number = models.CharField(max_length=50)
    ordered_items = models.ManyToManyField('OrderedProducts')

class Message(models.Model):
    id = models.UUIDField(primary_key = True, default = uuid.uuid4, editable = False)
    created_date = models.DateTimeField(auto_now_add = True, blank = True)
    content = models.TextField(validators=[validate_content_message])
    user = models.ForeignKey(User, default=1, on_delete=models.CASCADE)
    room_name = models.CharField(max_length=50, default='')