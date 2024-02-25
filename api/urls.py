from roles.views.roles import AllMemberAPI,MemberAPI,AllExportRequest,ExportRequestDownload
from location.views.location import AllSystemLocationAPI,SystemLocationAPI,AllLocationSettingsAPI,LocationSettingsAPI
from account.views.auth import UserTokenView
from shift.views.shift import AllShiftAPI,ShiftAPI,AllShiftScheduleLogAPI,ShiftScheduleLogAPI
from frimage.views.frimage import AllFrImageAPI,FriImageAPI
from memberscan.views.memberscan import AllMemberScanAPI,AllAttendanceAPI
from django.urls import path
urlpatterns = [
    path("user/token",UserTokenView.as_view(),name="user-token"),
    path("member/",AllMemberAPI.as_view(),name="member-get-post"),
    path("member/<uuid:uuid>/",MemberAPI.as_view(),name="member-update-delete"),
    path("system-location/",AllSystemLocationAPI.as_view(),name="system-location-get-post"),
    path("system-location/<uuid:uuid>/",SystemLocationAPI.as_view(),name="system-update-delete"),
    path("shift/",AllShiftAPI.as_view(),name="shift-get-post"),
    path("shift/<uuid:uuid>/",ShiftAPI.as_view(),name="shift-update-delete"),
    path("shift-schedule-log/",AllShiftScheduleLogAPI.as_view(),name="shift-schedule-log-get-post"),
    path("shift-schedule-log/<uuid:uuid>/",ShiftScheduleLogAPI.as_view(),name="shift-schedule-update-delete"),
    path("fr-images/",AllFrImageAPI.as_view(),name="fri-image-get-post"),
    path("fr-images/<uuid:uuid>/",FriImageAPI.as_view(),name="fri-image-update-delete"),
    path("location-settings/shift-schedule-log/",AllLocationSettingsAPI.as_view(),name="location-settings-get"),
   
    path("location-settings/shift-schedule-log/<uuid:uuid>/",LocationSettingsAPI.as_view(),name="location-setting-post-update-delete"),
    path("scan/",AllMemberScanAPI.as_view(),name="scan-get-post"),
    path('attendance/',AllAttendanceAPI.as_view(),name="attendance=get"),
    path("exportrequest/<uuid:uuid>/",AllExportRequest.as_view(),name="export-request-get"),
    path("exportrequest/download/<str:filename>/",ExportRequestDownload.as_view(),name="export-request-download")

]
