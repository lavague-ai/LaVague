from lavague.action_engine import RemoteActionEngine

rae = RemoteActionEngine()
print(rae.get_action("scroll by 50 pixels", "<html></html>"))
for line in rae.get_action_streaming("scroll by 50 pixels, then print in python the first 15 lines of the first chapter of hamlet ", "<html></html>"):
    print(line)