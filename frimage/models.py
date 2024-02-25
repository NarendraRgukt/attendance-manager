from django.db import models
import uuid
from roles import models as model
class FRImage(models.Model):
    uuid=models.UUIDField(primary_key=True,editable=False,default=uuid.uuid4)
    member=models.ForeignKey(model.Member,on_delete=models.CASCADE,related_name="frimage")
    image=models.ImageField(upload_to="media/",null=True)
    updated_at=models.DateTimeField(auto_now=True)
    organization=models.ForeignKey(model.Organization,on_delete=models.CASCADE,related_name="frimage")

    def __str__(self):
        return self.member.user.username
    

    