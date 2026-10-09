import mimetypes
from pathlib import Path

from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def serve_profile_media(request, path):
    media_root = Path(settings.MEDIA_ROOT).resolve()
    file_path = (media_root / path).resolve()
    if not file_path.is_relative_to(media_root) or not file_path.is_file():
        raise Http404
    content_type, _ = mimetypes.guess_type(file_path.name)
    return FileResponse(file_path.open('rb'), content_type=content_type or 'application/octet-stream')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [path('media/<path:path>', serve_profile_media, name='profile-media')]
