from collections import MutableSequence


class Navigator(MutableSequence):
    
    def __init__ (self, pages):
        self.pages = list(pages)
        self.index = 0

    def __iter__ (self):
        return self

    def __next__ (self):
        try:
            item = self.pages[self.index]
        except IndexError:
            raise StopIteration()
        self.index += 1
        return item
    
    def prev(self):
        try:
            item = self.pages[self.index]
        except IndexError:
            raise StopIteration()
        self.index += 1
        return item
    
    def current(self, obj=None):
        return self.pages[self.index]
    
    def first(self):
        return self.pages[0]   
    
    def last(self):
        return self.pages[-1]   

    # search by label seq 
    def search(self, page_id):
      for i in self.pages:
          if i[0] == page_id:
             return i
