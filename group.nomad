task "cantaloupe" {
  driver = "docker"

  lifecycle {
    hook = "prestart"
    sidecar = true
  }

  config {
    image = "uclalibrary/cantaloupe:5.0.5-7"
    ports = [ "cantaloupe" ]
    mount {
      type = "bind"
      target = "/etc/cantaloupe/cantaloupe.properties"
      source = "cantaloupe.properties"
      readonly = true
      bind_options {
        propagation = "rshared"
      }
    }
  }

  template {
    data = <<EOF
temp_pathname =

http.enabled = true
http.host = 0.0.0.0
http.port = 8182
http.http2.enabled = false

https.enabled = false
https.host = 0.0.0.0
https.port = 8183
https.http2.enabled = false

https.key_store_type = JKS
https.key_store_password = myPassword
https.key_store_path = /path/to/keystore.jks
https.key_password = myPassword

http.accept_queue_limit =

base_uri =

slash_substitute =

max_pixels = 100000000

max_scale = 1.0

print_stack_trace_on_error_pages = true


delegate_script.enabled = false

delegate_script.pathname = delegates.rb

delegate_script.cache.enabled = false


endpoint.iiif.1.enabled = false

endpoint.iiif.2.enabled = true

endpoint.iiif.content_disposition = inline

endpoint.iiif.min_size = 64

endpoint.iiif.min_tile_size = 512

endpoint.iiif.2.restrict_to_sizes = false

endpoint.admin.enabled = false
endpoint.admin.username = admin
endpoint.admin.secret =

endpoint.api.enabled = false

endpoint.api.username =
endpoint.api.secret =


source.static = HttpSource

source.delegate = false


FilesystemSource.lookup_strategy = BasicLookupStrategy

FilesystemSource.BasicLookupStrategy.path_prefix = /home/myself/images/

FilesystemSource.BasicLookupStrategy.path_suffix =


HttpSource.allow_insecure = false

HttpSource.request_timeout =

HttpSource.lookup_strategy = BasicLookupStrategy

HttpSource.BasicLookupStrategy.url_prefix = http://archive.org/download/

HttpSource.BasicLookupStrategy.url_suffix =

HttpSource.BasicLookupStrategy.auth.basic.username =
HttpSource.BasicLookupStrategy.auth.basic.secret =

HttpSource.chunking.enabled = true

HttpSource.chunking.chunk_size = 512K

HttpSource.chunking.cache.enabled = true

HttpSource.chunking.cache.max_size = 5M


S3Source.endpoint =

S3Source.access_key_id =
S3Source.secret_key =

S3Source.lookup_strategy = BasicLookupStrategy

S3Source.BasicLookupStrategy.bucket.name =

S3Source.BasicLookupStrategy.path_prefix =

S3Source.BasicLookupStrategy.path_suffix =

S3Source.chunking.enabled = true

S3Source.chunking.chunk_size = 512K

S3Source.chunking.cache.enabled = true

S3Source.chunking.cache.max_size = 5M


AzureStorageSource.account_name =

AzureStorageSource.account_key =

AzureStorageSource.container_name =

AzureStorageSource.lookup_strategy = BasicLookupStrategy

AzureStorageSource.chunking.enabled = true

AzureStorageSource.chunking.chunk_size = 512K

AzureStorageSource.chunking.cache.enabled = true

AzureStorageSource.chunking.cache.max_size = 5M



JdbcSource.url = jdbc:postgresql://localhost:5432/my_database
JdbcSource.user = postgres
JdbcSource.password = postgres

JdbcSource.connection_timeout = 10



processor.selection_strategy = AutomaticSelectionStrategy


processor.ManualSelectionStrategy.avi = FfmpegProcessor
processor.ManualSelectionStrategy.bmp =
processor.ManualSelectionStrategy.dcm = ImageMagickProcessor
processor.ManualSelectionStrategy.flv = FfmpegProcessor
processor.ManualSelectionStrategy.gif =
processor.ManualSelectionStrategy.jp2 = KakaduNativeProcessor
processor.ManualSelectionStrategy.jpg =
processor.ManualSelectionStrategy.mov = FfmpegProcessor
processor.ManualSelectionStrategy.mp4 = FfmpegProcessor
processor.ManualSelectionStrategy.mpg = FfmpegProcessor
processor.ManualSelectionStrategy.pdf = PdfBoxProcessor
processor.ManualSelectionStrategy.png =
processor.ManualSelectionStrategy.tif =
processor.ManualSelectionStrategy.webm = FfmpegProcessor
processor.ManualSelectionStrategy.webp = ImageMagickProcessor

processor.ManualSelectionStrategy.fallback = Java2dProcessor


processor.stream_retrieval_strategy = StreamStrategy

processor.fallback_retrieval_strategy = DownloadStrategy

processor.dpi = 150

processor.background_color = white

processor.downscale_filter = bicubic
processor.upscale_filter = bicubic

processor.sharpen = 0

processor.metadata.preserve = false

processor.metadata.respect_orientation = false

processor.jpg.progressive = true

processor.jpg.quality = 80

processor.tif.compression = LZW


processor.imageio.bmp.reader =
processor.imageio.gif.reader =
processor.imageio.gif.writer =
processor.imageio.jpg.reader =
processor.imageio.jpg.writer =
processor.imageio.png.reader =
processor.imageio.png.writer =
processor.imageio.tif.reader =
processor.imageio.tif.writer =


FfmpegProcessor.path_to_binaries =


GraphicsMagickProcessor.path_to_binaries =


ImageMagickProcessor.path_to_binaries =


KakaduDemoProcessor.path_to_binaries =


OpenJpegProcessor.path_to_binaries =


cache.client.enabled = true

cache.client.max_age = 2592000
cache.client.shared_max_age =
cache.client.public = true
cache.client.private = false
cache.client.no_cache = false
cache.client.no_store = false
cache.client.must_revalidate = false
cache.client.proxy_revalidate = false
cache.client.no_transform = true



cache.server.source = FilesystemCache

cache.server.source.ttl_seconds = 604800

cache.server.derivative.enabled = true

cache.server.derivative = FilesystemCache

cache.server.derivative.ttl_seconds = 604800

cache.server.info.enabled = true

cache.server.purge_missing = false

cache.server.resolve_first = false

cache.server.worker.enabled = false

cache.server.worker.interval = 86400


FilesystemCache.pathname = /var/cache/cantaloupe

FilesystemCache.dir.depth = 3

FilesystemCache.dir.name_length = 2


HeapCache.target_size = 2G

HeapCache.persist = false

HeapCache.persist.filesystem.pathname = /var/cache/cantaloupe/heap.cache


JdbcCache.url = jdbc:postgresql://localhost:5432/cantaloupe
JdbcCache.user = postgres
JdbcCache.password =

JdbcCache.connection_timeout = 10

JdbcCache.derivative_image_table = derivative_cache
JdbcCache.info_table = info_cache


S3Cache.endpoint =

S3Cache.access_key_id =
S3Cache.secret_key =

S3Cache.bucket.name =

S3Cache.object_key_prefix =

S3Cache.max_connections =


AzureStorageCache.account_name =
AzureStorageCache.account_key =

AzureStorageCache.container_name =

AzureStorageCache.object_key_prefix =


RedisCache.host = redis
RedisCache.port = 6379
RedisCache.ssl = false
RedisCache.password =
RedisCache.database = 0


overlays.enabled = false

overlays.strategy = BasicStrategy

overlays.BasicStrategy.type = image

overlays.BasicStrategy.image = /path/to/overlay.png

overlays.BasicStrategy.string = Copyright © My Great Organization\nAll rights reserved.

overlays.BasicStrategy.string.font = Helvetica

overlays.BasicStrategy.string.font.size = 24

overlays.BasicStrategy.string.font.min_size = 18

overlays.BasicStrategy.string.font.weight = 1.0

overlays.BasicStrategy.string.glyph_spacing = 0.02

overlays.BasicStrategy.string.color = white

overlays.BasicStrategy.string.stroke.color = black

overlays.BasicStrategy.string.stroke.width = 1

overlays.BasicStrategy.string.background.color = rgba(0, 0, 0, 100)

overlays.BasicStrategy.position = bottom right

overlays.BasicStrategy.inset = 10

overlays.BasicStrategy.output_width_threshold = 400

overlays.BasicStrategy.output_height_threshold = 300


redaction.enabled = false



log.application.level = debug

log.application.ConsoleAppender.enabled = true

log.application.FileAppender.enabled = false
log.application.FileAppender.pathname = /path/to/logs/application.log

log.application.RollingFileAppender.enabled = false
log.application.RollingFileAppender.pathname = /path/to/logs/application.log
log.application.RollingFileAppender.policy = TimeBasedRollingPolicy
log.application.RollingFileAppender.TimeBasedRollingPolicy.filename_pattern = /path/to/logs/application-%d{yyyy-MM-dd}.log
log.application.RollingFileAppender.TimeBasedRollingPolicy.max_history = 30

log.application.SyslogAppender.enabled = false
log.application.SyslogAppender.host =
log.application.SyslogAppender.port = 514
log.application.SyslogAppender.facility = LOCAL0



log.error.FileAppender.enabled = false
log.error.FileAppender.pathname = /path/to/logs/error.log

log.error.RollingFileAppender.enabled = false
log.error.RollingFileAppender.pathname = /path/to/logs/error.log
log.error.RollingFileAppender.policy = TimeBasedRollingPolicy
log.error.RollingFileAppender.TimeBasedRollingPolicy.filename_pattern = /path/to/logs/error-%d{yyyy-MM-dd}.log
log.error.RollingFileAppender.TimeBasedRollingPolicy.max_history = 30


log.access.ConsoleAppender.enabled = false

log.access.FileAppender.enabled = false
log.access.FileAppender.pathname = /path/to/logs/access.log

log.access.RollingFileAppender.enabled = false
log.access.RollingFileAppender.pathname = /path/to/logs/access.log
log.access.RollingFileAppender.policy = TimeBasedRollingPolicy
log.access.RollingFileAppender.TimeBasedRollingPolicy.filename_pattern = /path/to/logs/access-%d{yyyy-MM-dd}.log
log.access.RollingFileAppender.TimeBasedRollingPolicy.max_history = 30

log.access.SyslogAppender.enabled = false
log.access.SyslogAppender.host =
log.access.SyslogAppender.port = 514
log.access.SyslogAppender.facility = LOCAL0

EOF
    destination = "cantaloupe.properties"
    change_mode   = "signal"
    change_signal = "SIGHUP"
  }

  resources {
    cpu = 8000
    memory = 4096
  }
}
