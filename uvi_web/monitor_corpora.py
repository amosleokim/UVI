import pyinotify
import build_mongo_collections

watch_manager = pyinotify.WatchManager()

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_MODIFY(self, event):
        print(event.wd)
        if event.wd == 1:
            build_mongo_collections.build_verbnet_collection()
        elif event.wd == 2:
            build_mongo_collections.build_propbank_collection()
        elif event.wd == 3:
            build_mongo_collections.build_framenet_collection()

    def process_IN_DELETE(self, event):
        if event.wd == 1:
            build_mongo_collections.build_verbnet_collection()
        elif event.wd == 2:
            build_mongo_collections.build_propbank_collection()
        elif event.wd == 3:
            build_mongo_collections.build_framenet_collection()
    def process_IN_CREATE(self, event):
        if event.wd == 1:
            build_mongo_collections.build_verbnet_collection()
        elif event.wd == 2:
            build_mongo_collections.build_propbank_collection()
        elif event.wd == 3:
            build_mongo_collections.build_framenet_collection()

handler = EventHandler()
notifier = pyinotify.Notifier(watch_manager, handler)

wdd_vn = watch_manager.add_watch('../corpora/verbnet', pyinotify.ALL_EVENTS)
wdd_vn_refs = watch_manager.add_watch('../reference_docs', pyinotify.ALL_EVENTS)
wdd_pb = watch_manager.add_watch('../corpora/propbank/frames', pyinotify.ALL_EVENTS)
wdd_fn = watch_manager.add_watch('../corpora/framenet', pyinotify.ALL_EVENTS)
#wdd_on = watch_manager.add_watch('../corpora/ontonotes', pyinotify.ALL_EVENTS)

print('Monitoring corpora for changes...')

notifier.loop()