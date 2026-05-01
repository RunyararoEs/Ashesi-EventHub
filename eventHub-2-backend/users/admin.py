from django.contrib import admin
from users.models import User, Student, Club, ClubAdmin, SystemAdmin, ClubAdminTransferRequest

admin.site.register(User)
admin.site.register(Student)
admin.site.register(Club)
admin.site.register(ClubAdmin)
admin.site.register(SystemAdmin)
admin.site.register(ClubAdminTransferRequest)