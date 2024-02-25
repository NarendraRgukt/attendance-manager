from typing import Any
from django.contrib import admin
from account.models import User

class UserAdmin(admin.ModelAdmin):
    list_display=['uuid','id','username','email','is_active','is_staff','is_superuser']
    fieldsets=(
        ("Authentication",{'fields':('username','email','password')}),
        (
            "Personal Details",{
                'fields':('first_name','last_name')
            }
        ),
        (
            "Permissions",{
                'fields':(
                    'is_active','is_staff','is_superuser'
                )
            }
        ),
        (
            'Login Details',{
                'fields':(
                    'last_login',
                )
            }
        )
        
        )
    readonly_fields=['last_login']

    def save_model(self, request: Any, obj: Any, form: Any, change: Any) -> None:
        password=form.cleaned_data.get('password')
        obj.set_password(password)
        if password and password != obj.password:
            obj.set_password(password)

        
        super().save_model(request, obj, form, change)

admin.site.register(User,UserAdmin)

    
